// Pass 3: Convert bracket property access to dot notation
// obj['prop'] -> obj.prop (only when 'prop' is a valid JS identifier)

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
      }
    };
  }
};
