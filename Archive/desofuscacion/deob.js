import { parse } from '@babel/parser';
import _traverse from '@babel/traverse';
const traverse = _traverse.default || _traverse;
import _generate from '@babel/generator';
const generate = _generate.default || _generate;
import fs from 'fs';

const source = fs.readFileSync('obfuscated.js', 'utf8');
const parserOpts = {
    sourceType: 'script',
    plugins: ['optionalChaining', 'nullishCoalescingOperator'],
    allowReturnOutsideFunction: true,
};

// PRE-PASS: collect literal arrays
const preAst = parse(source, parserOpts);
const arrays = new Map();
traverse(preAst, {
    VariableDeclarator(path) {
        const { id, init } = path.node;
        if (id.type !== 'Identifier' || init?.type !== 'ArrayExpression') return;
        const els = init.elements;
        if (els.length < 2) return;
        if (!els.every(el => el === null || el?.type === 'StringLiteral' || el?.type === 'NumericLiteral' || el?.type === 'NullLiteral')) return;
        arrays.set(id.name, els.map(el => el?.value ?? null));
    }
});

// MAIN PASS
const ast = parse(source, parserOpts);
const S = { hex: 0, resolve: 0, arrays: 0, ternary: 0, void0: 0, yoda: 0, dot: 0, deadSw: 0, bugs: 0, comma: 0, super: 0, junk: 0 };
const resolvedArrays = new Set();
const mainArrayPaths = new Map();

traverse(ast, {
    StringLiteral(path) {
        if (path.node.extra) { S.hex++; delete path.node.extra; }
    },
    VariableDeclarator(path) {
        if (path.node.id.type === 'Identifier' && arrays.has(path.node.id.name)) {
            mainArrayPaths.set(path.node.id.name, { declPath: path, parentPath: path.parentPath });
        }
    },
    MemberExpression(path) {
        const { property, computed } = path.node;
        if (computed && path.node.object.type === 'Identifier' && property.type === 'NumericLiteral') {
            const vals = arrays.get(path.node.object.name);
            if (vals) {
                const i = property.value;
                if (i >= 0 && i < vals.length) {
                    S.resolve++;
                    resolvedArrays.add(path.node.object.name);
                    const v = vals[i];
                    if (typeof v === 'string') path.replaceWith({ type: 'StringLiteral', value: v });
                    else if (typeof v === 'number') path.replaceWith({ type: 'NumericLiteral', value: v });
                    else path.replaceWith({ type: 'NullLiteral' });
                    return;
                }
            }
        }
        // Also convert bracket→dot in AST
        if (computed && property.type === 'StringLiteral' && /^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(property.value)) {
            path.node.computed = false;
            path.node.property = { type: 'Identifier', name: property.value };
        }
    },
    UnaryExpression(path) {
        if (path.node.operator === 'void') {
            const arg = path.node.argument;
            let isZero = false;
            if (arg.type === 'NumericLiteral' && arg.value === 0) isZero = true;
            if (arg.type === 'MemberExpression' && arg.object.type === 'Identifier' && arg.property.type === 'NumericLiteral') {
                const vals = arrays.get(arg.object.name);
                if (vals && vals[arg.property.value] === 0) isZero = true;
            }
            if (isZero) { S.void0++; path.replaceWith({ type: 'Identifier', name: 'undefined' }); }
        }
        if (path.node.operator === '!') {
            const a = path.node.argument;
            let v;
            if (a.type === 'BooleanLiteral') v = !a.value;
            else if (a.type === 'NumericLiteral') v = !a.value;
            else if (a.type === 'NullLiteral') v = true;
            else if (a.type === 'StringLiteral') v = a.value === '';
            if (v !== undefined) path.replaceWith({ type: 'BooleanLiteral', value: v });
        }
    },
    BinaryExpression(path) {
        const { left, right, operator } = path.node;
        if (left.type === 'StringLiteral' && right.type === 'UnaryExpression' && right.operator === 'typeof') {
            const t = left.value;
            if (['function', 'object', 'string', 'number', 'boolean', 'undefined'].includes(t)) {
                S.yoda++;
                path.node.left = right.argument;
                path.node.operator = operator === '==' ? '===' : operator === '!=' ? '!==' : operator;
                path.node.right = { type: 'StringLiteral', value: t };
            }
        }
        if (left.type === 'NullLiteral' && (operator === '!==' || operator === '===')) {
            S.yoda++;
            path.node.left = right;
            path.node.right = left;
        }
        if (left.type === 'UnaryExpression' && left.operator === 'typeof' && right.type === 'Identifier' && right.name === 'undefined') {
            S.bugs++;
            path.node.left = left.argument;
            path.node.right = { type: 'Identifier', name: 'undefined' };
        }
        if (left.type === 'StringLiteral' && right.type === 'StringLiteral' && left.value === right.value && (operator === '==' || operator === '===')) {
            S.bugs++;
            path.replaceWith({ type: 'BooleanLiteral', value: true });
        }
    },
    ConditionalExpression(path) {
        const t = path.node.test;
        let r;
        if (t.type === 'BooleanLiteral') r = t.value;
        else if (t.type === 'NumericLiteral') r = t.value !== 0;
        else if (t.type === 'NullLiteral') r = false;
        else if (t.type === 'StringLiteral') r = t.value !== '';
        if (r !== undefined) { S.ternary++; path.replaceWith(r ? path.node.consequent : path.node.alternate); }
    },
    CallExpression(path) {
        const c = path.node.callee;
        if (c.type === 'SequenceExpression' && c.expressions.length === 2 && c.expressions[0].type === 'NumericLiteral' && c.expressions[0].value === 0) {
            S.comma++;
            path.node.callee = c.expressions[1];
        }
    },
    ReturnStatement(path) {
        const a = path.node.argument;
        if (!a) return;
        if (a.type !== 'LogicalExpression' || a.operator !== '||') return;
        if (a.right.type !== 'ThisExpression') return;
        const l = a.left;
        if (l.type !== 'LogicalExpression' || l.operator !== '&&') return;
        if (l.left.type !== 'BinaryExpression' || l.left.operator !== '!==' || l.left.left.type !== 'NullLiteral') return;
        const r = l.right;
        if (r.type !== 'CallExpression') return;
        const cal = r.callee;
        const m = cal.type === 'MemberExpression' ? (cal.computed ? cal.property.value : cal.property.name) : null;
        if (m !== 'apply') return;
        S.super++;
        path.node.argument = { type: 'CallExpression', callee: { type: 'Super' }, arguments: [{ type: 'SpreadElement', argument: { type: 'Identifier', name: 'arguments' } }] };
    },
    SwitchStatement(path) {
        const seen = new Map(), rm = [];
        path.node.cases.forEach((c, i) => {
            if (!c.test) return;
            const k = generate(c.test).code;
            if (seen.has(k)) { rm.push(i); S.deadSw++; } else seen.set(k, i);
        });
        for (let i = rm.length - 1; i >= 0; i--) path.node.cases.splice(rm[i], 1);
    },
    VariableDeclaration(path) {
        if (path.node.declarations.every(d => {
            if (d.id.type !== 'Identifier') return false;
            const b = path.scope.getBinding(d.id.name);
            return b && b.references === 0;
        }) && path.node.declarations.length > 0) { S.junk++; path.remove(); }
    },
    Program: {
        exit(path) {
            for (const name of resolvedArrays) {
                const info = mainArrayPaths.get(name);
                if (!info) continue;
                try {
                    const { declPath, parentPath } = info;
                    if (parentPath?.node?.declarations?.length === 1) parentPath.remove();
                    else declPath.remove();
                    S.arrays++;
                } catch (e) { }
            }
        }
    },
});

// Generate code
let output = generate(ast, { retainLines: false, concise: false, comments: true }).code;

// POST-PROCESSING: bracket→dot on all remaining
const beforeBrackets = (output.match(/\["/g) || []).length;
output = output.replace(/([a-zA-Z_$)\]])\["([a-zA-Z_$][a-zA-Z0-9_$]*)"\]/g, (match, before, name) => {
    return before + '.' + name;
});
const afterBrackets = (output.match(/\["/g) || []).length;
S.dot = beforeBrackets - afterBrackets;

fs.writeFileSync('deobfuscated.js', output);

const total = Object.values(S).reduce((a, b) => a + b, 0);
console.log('='.repeat(60));
console.log('DEOB.JS — Full Pipeline');
console.log('='.repeat(60));
for (const [k, v] of Object.entries(S)) console.log(`  ${k.padEnd(14)} ${v}`);
console.log(`  ${'TOTAL'.padEnd(14)} ${total}`);
console.log(`  ${'output'.padEnd(14)} ${output.length} bytes`);
console.log(`  ${'brackets'.padEnd(14)} ${afterBrackets} remaining`);
console.log('='.repeat(60));