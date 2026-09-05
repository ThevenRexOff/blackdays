// Pass 2: Resolve per-function string lookup tables
// Two separate traversals: first collect, then resolve.
// This guarantees all arrays are registered before any lookups are resolved.

// Shared state between phases
const arrayBindings = new Map();

export default [
  // Phase 1: collect every literal array declaration
  {
    name: 'p2-collect-arrays',
    plugin() {
      return {
        VariableDeclarator(path) {
          const { id, init } = path.node;
          if (id.type !== 'Identifier' || init?.type !== 'ArrayExpression') return;
          const elements = init.elements;
          if (elements.length < 2) return;
          const allLiterals = elements.every(el =>
            el === null || el.type === 'StringLiteral' || el.type === 'NumericLiteral'
          );
          if (!allLiterals) return;
          const values = elements.map(el => el === null ? null : el.value);
          arrayBindings.set(id.name, { values, path, refs: 0 });
        }
      };
    }
  },
  // Phase 2: resolve indexed lookups and remove used arrays
  {
    name: 'p2-resolve-lookups',
    plugin() {
      return {
        MemberExpression(path) {
          const { object, property, computed } = path.node;
          if (!computed || object.type !== 'Identifier' || property.type !== 'NumericLiteral') return;
          const info = arrayBindings.get(object.name);
          if (!info) return;
          const idx = property.value;
          if (idx < 0 || idx >= info.values.length) return;
          info.refs++;
          const val = info.values[idx];
          if (val === null) {
            path.replaceWith({ type: 'NullLiteral' });
          } else if (typeof val === 'string') {
            path.replaceWith({ type: 'StringLiteral', value: val });
          } else if (typeof val === 'number') {
            path.replaceWith({ type: 'NumericLiteral', value: val });
          }
        },
        Program: {
          exit() {
            const toRemove = [];
            for (const [, info] of arrayBindings) {
              if (info.refs > 0) toRemove.push(info.path);
            }
            for (let i = toRemove.length - 1; i >= 0; i--) {
              const p = toRemove[i];
              const parent = p.parentPath;
              if (parent?.node?.declarations?.length === 1) {
                parent.remove();
              } else {
                p.remove();
              }
            }
            arrayBindings.clear();
          }
        }
      };
    }
  }
];
