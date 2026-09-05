// Pass 4: Remove dead code and junk
// - Unused variable declarations (decoy functions, random constants)
// - Standalone expression statements that are just literals

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
        // Remove standalone literal expressions
        if (expr.type === 'NumericLiteral' || expr.type === 'StringLiteral') {
          path.remove();
        }
      }
    };
  }
};
