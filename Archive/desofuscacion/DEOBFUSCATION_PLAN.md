# Deobfuscation Plan: Amazon FWCIM Fingerprinting JS

## Overview

Multi-pass Babel plugin pipeline to deobfuscate `/home/thevenrex/Downloads/amazon_fp/ofuscated.js` — a Webpack 3/4 bundle with 78 modules, ~678 lines, ~268KB.

---

## Project Setup

### Directory Structure
```
amazon_fp/
├── ofuscated.js              # Input (read-only reference)
├── package.json
├── deobfuscate.mjs           # Main runner script
├── passes/
│   ├── p1-hex-decode.mjs     # Pass 1: String literal hex decoding
│   ├── p2-resolve-lookups.mjs # Pass 2: Inline lookup table values
│   ├── p3-inline-props.mjs   # Pass 3: Replace obj[arr[idx]] → obj.prop
│   ├── p4-remove-junk.mjs    # Pass 4: Dead code & junk removal
│   ├── p5-flatten-expressions.mjs # Pass 5: Comma expressions, void 0, etc.
│   └── p6-rename-vars.mjs    # Pass 6: Human-readable variable renaming
└── test-runner.mjs           # Snapshot/execution comparison
```

### package.json
```json
{
  "type": "module",
  "scripts": {
    "deobfuscate": "node deobfuscate.mjs",
    "test": "node test-runner.mjs"
  },
  "dependencies": {
    "@babel/parser": "^7.24.0",
    "@babel/traverse": "^7.24.0",
    "@babel/generator": "^7.24.0",
    "@babel/types": "^7.24.0"
  }
}
```

### deobfuscate.mjs (runner)
```js
import { parse } from '@babel/parser';
import traverse from '@babel/traverse';
import generate from '@babel/generator';
import fs from 'fs';

import pass1 from './passes/p1-hex-decode.mjs';
import pass2 from './passes/p2-resolve-lookups.mjs';
import pass3 from './passes/p3-inline-props.mjs';
import pass4 from './passes/p4-remove-junk.mjs';
import pass5 from './passes/p5-flatten-expressions.mjs';
import pass6 from './passes/p6-rename-vars.mjs';

const source = fs.readFileSync('ofuscated.js', 'utf8');

const passes = [pass1, pass2, pass3, pass4, pass5, pass6];

let code = source;
for (const { name, plugin } of passes) {
  console.log(`Running ${name}...`);
  const ast = parse(code, {
    sourceType: 'script',
    plugins: ['optionalChaining', 'nullishCoalescingOperator'],
    allowReturnOutsideFunction: true,
  });
  traverse(ast, plugin());
  code = generate(ast, { retainLines: true }).code;
  fs.writeFileSync(`output-after-${name}.js`, code);
  console.log(`  → ${name} complete (${code.length} bytes)`);
}

fs.writeFileSync('deobfuscated.js', code);
console.log('Done. Output: deobfuscated.js');
```

**Parser config notes:**
- `sourceType: 'script'` (not module) because Webpack bundles use IIFE + `var`
- `allowReturnOutsideFunction: true` because the outermost wrapper is an IIFE passed to AmazonUIPageJS
- No JSX/TypeScript plugins needed

---

## Pass 1: Hex String Literal Decoding

**Goal:** Convert all `\xHH` escape sequences in string literals to their readable characters.

### AST Pattern
Every `StringLiteral` node where the `extra.raw` contains `\x` escape sequences.

### Transformation
```js
// p1-hex-decode.mjs
export default {
  name: 'p1-hex-decode',
  plugin() {
    return {
      StringLiteral(path) {
        const node = path.node;
        // Babel's parser already decodes \xHH to actual chars in node.value
        // but the raw representation keeps them encoded. Force re-render:
        delete node.extra;  // Remove extra.raw with \x escapes
        // Babel generator will re-emit using the decoded value
        // For very long strings, this produces readable output
      },
      Directive(path) {
        // Preserve "use strict" directives — don't touch them
      }
    };
  }
};
```

### Key Insight
Babel's parser **already decodes** `\x63\x6f\x6c\x6c\x65\x63\x74` into `"collect"` in `node.value`. The `\x` encoding lives in `node.extra.raw`. By deleting `node.extra`, we force `@babel/generator` to re-serialize using the decoded `node.value`, which produces plain strings.

### Edge Cases
- **`'use strict'` directives** (lines 103, 135, etc.) — must not be touched; they're actual directives, not just strings
- **Regular expressions** with `\x` escapes in their pattern — these are `RegExpLiteral` nodes, not `StringLiteral`, so they're unaffected
- **Template literals** — none observed in this file
- **Strings containing only ASCII-unsafe characters** — generator will use escapes for non-printable chars, but all hex-encoded strings here decode to readable ASCII

### Expected Result
```js
// Before: exports['\x5f\x5f\x65\x73\x4d\x6f\x64\x75\x6c\x65']=1;
// After:  exports['__esModule']=1;

// Before: var _lII1=['\x63\x6f\x6c\x6c\x65\x63\x74','\x70\x72\x6f\x74\x6f\x74\x79\x70\x65','\x64\x61\x74\x61',null];
// After:  var _lII1=['collect','prototype','data',null];
```

---

## Pass 2: Resolve Per-Function Lookup Tables

**Goal:** Replace `lookupArray[index]` references with the actual string values from the array.

### AST Pattern
1. `VariableDeclarator` where `init` is an `ArrayExpression` containing only `StringLiteral` and/or `NumericLiteral` elements
2. `MemberExpression` where `object` is the `Identifier` of that array, and `property` is a `NumericLiteral`

This pattern appears ~452 times in the file:
```js
var _lII1=['collect','prototype','data',null];
// Then: _lII1[0] → 'collect', _lII1[1] → 'prototype'
```

### Transformation
```js
// p2-resolve-lookups.mjs
export default {
  name: 'p2-resolve-lookups',
  plugin() {
    // Map: binding name → array of resolved values
    const arrayBindings = new Map();

    return {
      VariableDeclarator(path) {
        const { id, init } = path.node;
        if (id.type !== 'Identifier' || init?.type !== 'ArrayExpression') return;

        const elements = init.elements;
        // Only track arrays that are purely string/numeric/null literal lookup tables
        // Must have at least 2 elements (otherwise pointless)
        if (elements.length < 2) return;

        const allLiterals = elements.every(el =>
          el === null ||
          el.type === 'StringLiteral' ||
          el.type === 'NumericLiteral'
        );
        if (!allLiterals) return;

        const values = elements.map(el => el === null ? null : el.value);
        arrayBindings.set(id.name, { values, declaratorPath: path });
      },

      MemberExpression(path) {
        const { object, property, computed } = path.node;
        if (!computed) return;
        if (object.type !== 'Identifier') return;
        if (property.type !== 'NumericLiteral') return;

        const info = arrayBindings.get(object.name);
        if (!info) return;

        const idx = property.value;
        if (idx < 0 || idx >= info.values.length) return;

        const val = info.values[idx];
        if (val === null) {
          path.replaceWith(path.type === 'MemberExpression'
            ? { type: 'NullLiteral' }
            : path.node);  // null literal
        } else if (typeof val === 'string') {
          path.replaceWith({ type: 'StringLiteral', value: val });
        } else if (typeof val === 'number') {
          path.replaceWith({ type: 'NumericLiteral', value: val });
        }
      },

      // After all lookups resolved, remove unused array declarations
      Program: {
        exit(path) {
          for (const [name, { declaratorPath }] of arrayBindings) {
            const binding = declaratorPath.scope.getBinding(name);
            if (binding && binding.references === 0) {
              // Check if parent is just a VariableDeclaration with one declarator
              const parent = declaratorPath.parentPath;
              if (parent.node.declarations.length === 1) {
                parent.remove();
              } else {
                declaratorPath.remove();
              }
            }
          }
        }
      }
    };
  }
};
```

### Edge Cases
- **Mixed-type arrays**: Some arrays have strings AND numeric constants AND `null`. The resolver handles all three types.
- **Junk numeric values in arrays**: e.g., `[0.8410422588759491, 'document', 14707]` — these are dead-code noise. We resolve ALL lookups; the noise values are never referenced.
- **Arrays with non-literal elements**: Some inner arrays have function references or variable references — we skip these (only pure literal arrays).
- **Circular references**: Not possible here — lookup tables are IIFE-scoped and used linearly.
- **`0` index used as comma-expression padding**: Patterns like `(0, k['__awaiter'])(...)` — after resolving, this becomes `(0, k['__awaiter'])(...)` which is still valid. Pass 5 will clean this up.

### Expected Result
```js
// Before:
var _lII1=['collect','prototype','data',null];
function t(){this[_lII1[2]]=_lII1[3];}
return t[_lII1[1]][_lII1[0]]=function(){...};

// After:
function t(){this['data']=null;}
return t['prototype']['collect']=function(){...};
```

---

## Pass 3: Inline Property Access (obj[prop] → obj.prop)

**Goal:** Convert bracket property access with string literals to dot notation.

### AST Pattern
`MemberExpression` where `computed === true` and `property` is a `StringLiteral` that is a valid identifier.

### Transformation
```js
// p3-inline-props.mjs
export default {
  name: 'p3-inline-props',
  plugin() {
    return {
      MemberExpression(path) {
        const { property, computed } = path.node;
        if (!computed) return;
        if (property.type !== 'StringLiteral') return;

        const name = property.value;
        // Must be valid JS identifier
        if (/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(name)) {
          path.node.computed = false;
          path.node.property = { type: 'Identifier', name };
        }
        // Otherwise leave as bracket access (e.g., 'input[type="date"]')
      }
    };
  }
};
```

### Edge Cases
- **CSS selectors as strings**: e.g., `'input[type="date"]'` (seen in module 53's telemetry) — these are NOT valid identifiers, so they stay as bracket access. This is correct since they're used in `querySelectorAll` calls.
- **Property names with hyphens**: e.g., `'data-fwcim-id'` — stays as bracket access (correct behavior).
- **`exports['__esModule']`** — this is a valid identifier, gets converted to `exports.__esModule`.

### Expected Result
```js
// Before: t[_lII1[1]][_lII1[0]] = ...
// After (after pass 2): t['prototype']['collect'] = ...
// After pass 3: t.prototype.collect = ...

// Before: e[_oOo[5]][_oOo[7]](e,t)
// After pass 3: e.element.addEventListener(e,t)  (if resolved strings are valid identifiers)
```

---

## Pass 4: Remove Dead Code and Junk

**Goal:** Remove unused variable declarations (junk), decoy function assignments, and unreachable code.

### AST Patterns & Transformations

#### 4a. Remove unused variable declarations
```js
// After pass 2, many lookup arrays are removed if unused.
// Also remove standalone assignments to never-referenced variables:
var _lIll1Ii1 = _00Qo[2];  // Assigned but never used

// Pattern: VariableDeclarator where init is a Literal/Identifier and
// the binding has 0 references after pass 2.
```

#### 4b. Remove junk function declarations
```js
// Pattern: FunctionDeclaration or VariableDeclarator with FunctionExpression
// where the name has 0 references:
function _Q0QooOoo(_2ssZ2zSZ) { /* always returns a string literal */ }
// These are decoy functions assigned to unused variables.
```

#### 4c. Remove dead switch-case branches
```js
// Pattern: SwitchStatement where certain case values are provably dead:
//   switch(e.label) { case 'collectData': return [...]; case 3: ... }
// After lookup resolution, we can identify which cases are never triggered
// if the discriminant is statically known.
// However, since the discriminant is dynamic (e.label), we leave these.
```

#### 4d. Remove standalone junk expressions
```js
// Pattern: ExpressionStatement that is just an assignment to an unused var:
var _Z$$$2Ss2 = _ZS2[2];   // _ZS2[2] resolved to a number, var never used
```

### Implementation
```js
// p4-remove-junk.mjs
export default {
  name: 'p4-remove-junk',
  plugin() {
    return {
      VariableDeclaration(path) {
        const scope = path.scope;
        // Remove declarations where ALL declarators are unused
        const allUnused = path.node.declarations.every(decl => {
          if (decl.id.type !== 'Identifier') return false;
          const binding = scope.getBinding(decl.id.name);
          return binding && binding.references === 0;
        });
        if (allUnused && path.node.declarations.length > 0) {
          path.remove();
        }
      },

      ExpressionStatement(path) {
        const expr = path.node.expression;
        // Remove standalone numeric/string literal expressions
        if (expr.type === 'NumericLiteral' || expr.type === 'StringLiteral') {
          path.remove();
        }
      }
    };
  }
};
```

### Edge Cases
- **Variables used via `this[...]`**: Some variables are accessed as properties of `this`. The scope binding won't catch `this[varName]` as a reference. However, after Pass 2 resolves lookups, the `varName` references disappear.
- **Exports**: `exports['__esModule'] = 1` and `exports['default'] = bt` — these are side-effectful and must NOT be removed. They reference the `exports` parameter, not a local variable.
- **`var` hoisting**: Babel's scope analysis handles `var` hoisting correctly.
- **Variables referenced in catch blocks or with/eval**: Not present in this file.

### Expected Result
~52+ decoy function declarations and ~1,290 random constant assignments removed.

---

## Pass 5: Clean Up Expression Patterns

**Goal:** Simplify comma expressions, `void 0` arguments, and the `(0, fn)(...)` pattern.

### AST Patterns

#### 5a. Comma expressions: `(0, k['__awaiter'])(...)`
Pattern: `SequenceExpression` in a `CallExpression` callee position where the first element is `NumericLiteral(0)`.
```js
// Before: (0, k['__awaiter'])(this, ...)
// After:  k['__awaiter'](this, ...)
```

#### 5b. `void` expressions as arguments: `void _lII1[0]` → `undefined`
Pattern: `UnaryExpression` with `operator === 'void'` and argument that resolves to a constant.
```js
// Before: k['__awaiter'](this, void _lII1[0], void _lII1[0], function() {
// After:  k['__awaiter'](this, void 0, void 0, function() {
```

#### 5c. Simplify `void 0` to `undefined` (optional, readability)
```js
// Before: void 0
// After:  void 0  (leave as-is since this is standard JS)
```

#### 5d. Ternary expressions that are always true/false (dead branches)
```js
// Pattern: condition ? branchA : branchB
// where condition is resolved to a constant.
// e.g., null !== this['data'] ? [2, 4] : [1, this.collectData()]
// If condition is statically resolvable, inline the taken branch.
```

### Implementation
```js
// p5-flatten-expressions.mjs
export default {
  name: 'p5-flatten-expressions',
  plugin() {
    return {
      // (0, fn)(...) → fn(...)
      CallExpression(path) {
        const callee = path.node.callee;
        if (callee.type === 'SequenceExpression' &&
            callee.expressions.length === 2 &&
            callee.expressions[0].type === 'NumericLiteral' &&
            callee.expressions[0].value === 0) {
          path.node.callee = callee.expressions[1];
        }
      },

      // void <constant> → void 0
      UnaryExpression(path) {
        if (path.node.operator === 'void' &&
            path.node.argument.type !== 'NumericLiteral') {
          // Only simplify if the argument is a resolved literal
          if (path.node.argument.type === 'StringLiteral' ||
              path.node.argument.type === 'NullLiteral') {
            path.node.argument = { type: 'NumericLiteral', value: 0 };
          }
        }
      },

      // Ternary with constant condition
      ConditionalExpression(path) {
        const test = path.node.test;
        let result;
        if (test.type === 'NullLiteral') result = false;
        else if (test.type === 'BooleanLiteral') result = test.value;
        else if (test.type === 'NumericLiteral') result = test.value !== 0;

        if (result !== undefined) {
          path.replaceWith(result ? path.node.consequent : path.node.alternate);
        }
      },

      // !0 → true, !1 → false, !"" → true, etc. (prefix boolean simplification)
      UnaryExpression(path) {
        if (path.node.operator === '!') {
          const arg = path.node.argument;
          if (arg.type === 'BooleanLiteral') {
            path.replaceWith({ type: 'BooleanLiteral', value: !arg.value });
          } else if (arg.type === 'NumericLiteral') {
            path.replaceWith({ type: 'BooleanLiteral', value: !arg.value });
          } else if (arg.type === 'StringLiteral') {
            path.replaceWith({ type: 'BooleanLiteral', value: !arg.value });
          } else if (arg.type === 'NullLiteral') {
            path.replaceWith({ type: 'BooleanLiteral', value: true });
          }
        }
      }
    };
  }
};
```

### Edge Cases
- **`typeof` operator**: `typeof e[_oOo[5]]` — do NOT simplify `typeof` expressions. The `typeof` operator is special and its operand may reference undefined variables without throwing.
- **Short-circuit evaluation**: `(condition && doSomething())` — do NOT flatten these, as the right side may have side effects that should only execute when the condition is true.
- **Computed member access**: After pass 3, some bracket access remains for CSS selectors. These should be left alone.

### Expected Result
```js
// Before: (0, k['__awaiter'])(this, void _lII1[0], void _lII1[0], function(){
// After:  k['__awaiter'](this, void 0, void 0, function(){

// Before: null !== this['data'] ? [2, 4] : [1, this.collectData()]
// After:  [1, this.collectData()]  (since null !== null is false)
```

---

## Pass 6: Human-Readable Variable Renaming

**Goal:** Rename mangled identifiers to meaningful names based on usage patterns.

### Strategy
This is the hardest pass because we need heuristics. We'll do targeted renaming for the most common patterns observed in the file.

### Transformation Rules (by heuristic)

#### 6a. Property name → variable name
If a variable is only ever used as `this[varName]`, rename it to match its usage:
```js
// this[varName] always → varName becomes the property name
// e.g., var k; ... this[k] → this.key → rename k → key
```

#### 6b. Common patterns
```js
// Module 1 (bt class): _lII1[0]→'collect', _lII1[1]→'prototype', _lII1[2]→'data'
// After pass 2+3, the class methods are readable. Focus on top-level names:
var bt → CollectorData  (exports['default'] = bt, used as a class)
var me → EventListener  (has addEventListener/removeEventListener methods)
var Q  → QuerySelector  (has querySelectorAll, generateRandomId methods)
var L  → CrcCalculator   (has buildCrcTable, calculate methods)
var Je → Collector       (telemetry collector with keyCycles, mouseCycles)
```

#### 6c. Webpack require aliases
```js
var k = __webpack_require__(0);  → keep as k (it's the tslib helper module)
var Se = __webpack_require__(1); → keep (used for base class)
// These are internal module references, renaming them is low value
```

### Implementation
```js
// p6-rename-vars.mjs
export default {
  name: 'p6-rename-vars',
  plugin() {
    return {
      // Rename based on the 'this[x]' pattern
      AssignmentExpression(path) {
        const { left, right } = path.node;
        // Pattern: this[identifier] = something → infer the identifier name
        if (left.type === 'MemberExpression' &&
            left.object.type === 'ThisExpression' &&
            left.property.type === 'Identifier') {
          // Mark this identifier as a property name
          // (used in scope tracking, but full rename is complex)
        }
      },

      // Rename top-level module function names based on exports
      AssignmentExpression(path) {
        const { left, right } = path.node;
        // Pattern: exports['default'] = SomeClass
        if (left.type === 'MemberExpression' &&
            left.object.name === 'exports' &&
            left.property.value === 'default') {
          // The right side's name hints at the class purpose
          // (We can annotate but full auto-rename is out of scope)
        }
      }
    };
  }
};
```

**Practical note:** Full auto-rename is complex. For this file, the most impactful readability gains come from passes 1-5. Pass 6 is optional polish. A practical approach: after passes 1-5, manually inspect and add targeted renames as a final `sed`/string replacement step.

---

## Pass 6 (Alternative): Conservative Manual-Style Renaming

Instead of full auto-rename, do targeted replacements after all other passes:

```js
// After passes 1-5, the code is largely readable.
// Apply string replacements for remaining gibberish:
const renames = {
  // Top-level class names (derived from exports and constructor usage)
  'var bt=': 'var CollectorData=',
  'var me=': 'var EventListener=',
  // ... add more as identified after passes 1-5
};
```

This is simpler and less error-prone than AST-level renaming.

---

## Testing Strategy

### test-runner.mjs
```js
import { execSync } from 'child_process';
import fs from 'fs';
import vm from 'vm';

const original = fs.readFileSync('ofuscated.js', 'utf8');
const deobfuscated = fs.readFileSync('deobfuscated.js', 'utf8');

// 1. Syntax check: both files must parse without errors
function parseCheck(code, label) {
  try {
    new Function(code);
    console.log(`✓ ${label} parses successfully`);
    return true;
  } catch (e) {
    console.error(`✗ ${label} parse error: ${e.message}`);
    return false;
  }
}

parseCheck(original, 'Original');
parseCheck(deobfuscated, 'Deobfuscated');

// 2. Structural comparison: count exports, functions, modules
function countPatterns(code, regex) {
  return (code.match(regex) || []).length;
}

const origExports = countPatterns(original, /exports\['/g);
const deobfExports = countPatterns(deobfuscated, /exports\['/g) +
                     countPatterns(deobfuscated, /exports\./g);
console.log(`Original exports: ${origExports}`);
console.log(`Deobfuscated exports: ${deobfExports}`);

// 3. No new syntax errors introduced
// 4. File size should be significantly smaller (junk removed)
console.log(`Original: ${original.length} bytes`);
console.log(`Deobfuscated: ${deobfuscated.length} bytes`);
console.log(`Reduction: ${(1 - deobfuscated.length / original.length) * 100}%`);

// 5. String readability: check that known strings are now readable
const checks = [
  ['collect', deobfuscated.includes("'collect'")],
  ['prototype', deobfuscated.includes("'prototype'")],
  ['__esModule', deobfuscated.includes("'__esModule'") || deobfuscated.includes('.__esModule')],
  ['querySelectorAll', deobfuscated.includes("'querySelectorAll'") || deobfuscated.includes('.querySelectorAll')],
  ['createElement', deobfuscated.includes("'createElement'") || deobfuscated.includes('.createElement')],
];
checks.forEach(([str, ok]) => {
  console.log(`${ok ? '✓' : '✗'} Contains readable string: '${str}'`);
});

// 6. No remaining \x escape sequences in strings (excluding regex patterns)
const hexStrings = deobfuscated.match(/'[^']*\\x[0-9a-f]{2}[^']*'/g) || [];
console.log(`Remaining \\x escapes in strings: ${hexStrings.length}`);
```

### Execution Verification
For runtime correctness, we can't easily execute the file (it needs a browser environment with `window`, `document`, AmazonUIPageJS). Instead:

1. **AST snapshot test**: Before/after comparison of AST node counts
2. **String extraction test**: Verify all hex strings are decoded
3. **Module count test**: Verify all 78 modules are preserved
4. **Syntax validity test**: Both files must parse without errors

---

## Edge Cases & Risks Summary

| Risk | Mitigation |
|------|-----------|
| Pass 2 resolves a non-lookup array | Only track arrays with ≥2 elements, all literals |
| Pass 3 breaks computed access for CSS selectors | Only convert if string is valid JS identifier |
| Pass 4 removes side-effectful declarations | Only remove when ALL declarators in the declaration are unused |
| Pass 5 breaks short-circuit evaluation | Only simplify in non-side-effect positions |
| Pass 6 renames incorrectly | Make optional; passes 1-5 give the big wins |
| Webpack bootstrap code is mangled | The bootstrap (lines 28-97) uses plain strings, not obfuscated — passes won't break it |
| Module 74 (Base64 library) has its own code | It's a well-known library — passes 1-3 will make it more readable |
| Generator/async patterns (__awaiter/__generator) | These are TypeScript helpers in module 0 — left as-is, they're functional code |

---

## Execution Order & Dependencies

```
Pass 1 (hex decode)
    ↓
Pass 2 (resolve lookups)  ← depends on Pass 1 for string values
    ↓
Pass 3 (inline props)     ← depends on Pass 2 for string literals
    ↓
Pass 4 (remove junk)      ← depends on Pass 2 for unused array cleanup
    ↓
Pass 5 (clean expressions)← depends on Pass 2 for constant values
    ↓
Pass 6 (rename)           ← depends on all prior passes for readability
```

Each pass re-parses and re-generates. This is slower but ensures each pass works on clean, correct AST.
