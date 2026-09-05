// Pass 1: Decode hex escape sequences in string literals
// Babel's parser already decodes \xHH to actual chars in node.value
// but node.extra.raw keeps the encoded form. Deleting node.extra
// forces the generator to re-emit using the decoded value.

export default {
  name: 'p1-hex-decode',
  plugin() {
    return {
      StringLiteral(path) {
        const node = path.node;
        // Only touch strings that actually have hex escapes in their raw form
        if (node.extra && node.extra.raw && node.extra.raw.includes('\\x')) {
          delete node.extra;
        }
      }
    };
  }
};
