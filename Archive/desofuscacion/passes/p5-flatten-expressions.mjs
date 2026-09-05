// Pass 5: Clean up expression patterns
// - (0, fn)(...) -> fn(...)
// - !0 -> true, !1 -> false
// - Ternaries with constant condition -> inline branch

export default {
  name: 'p5-flatten-expressions',
  plugin() {
    return {
      // (0, fn)(...) -> fn(...)
      CallExpression(path) {
        const callee = path.node.callee;
        if (callee.type === 'SequenceExpression' &&
            callee.expressions.length === 2 &&
            callee.expressions[0].type === 'NumericLiteral' &&
            callee.expressions[0].value === 0) {
          path.node.callee = callee.expressions[1];
        }
      },

      // Boolean simplification: !0 -> true, !1 -> false, !null -> true, etc.
      UnaryExpression(path) {
        if (path.node.operator !== '!') return;

        const arg = path.node.argument;
        let value;

        if (arg.type === 'BooleanLiteral') value = !arg.value;
        else if (arg.type === 'NumericLiteral') value = !arg.value;
        else if (arg.type === 'StringLiteral') value = arg.value === '';
        else if (arg.type === 'NullLiteral') value = true;

        if (value !== undefined) {
          path.replaceWith({ type: 'BooleanLiteral', value });
        }
      },

      // Ternary with constant condition -> inline taken branch
      ConditionalExpression(path) {
        const test = path.node.test;
        let result;

        if (test.type === 'BooleanLiteral') result = test.value;
        else if (test.type === 'NumericLiteral') result = test.value !== 0;
        else if (test.type === 'NullLiteral') result = false;
        else if (test.type === 'StringLiteral') result = test.value !== '';

        if (result !== undefined) {
          path.replaceWith(result ? path.node.consequent : path.node.alternate);
        }
      }
    };
  }
};
