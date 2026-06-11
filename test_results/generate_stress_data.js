// [WFGY] Zone: SAFE | λ: 0.2 | Action: Node.js generator script reusing fake_GEN browser files
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const FAKE_GEN_DIR = 'D:/Projet/fake_GEN';
const OUTPUT_DIR = path.join(__dirname, 'stress_data');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// 1. Create a context and load lists.js, generators.js, formatters.js
const context = {
  globalThis: {},
  Math: Math,
  Date: Date,
  String: String,
  parseInt: parseInt,
  parseFloat: parseFloat,
  console: console
};
// Bind globalThis back to the context itself
context.globalThis = context;
vm.createContext(context);

function loadScript(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  // For lists.js, if it defines FAKE_DATA with const, we want it on global scope.
  // Replacing 'const FAKE_DATA =' with 'globalThis.FAKE_DATA =' ensures it's available in context.
  if (filePath.endsWith('lists.js')) {
    content = content.replace(/const\s+FAKE_DATA\s*=/, 'globalThis.FAKE_DATA =');
  }
  vm.runInContext(content, context, filePath);
}

console.log('[LOAD] Loading fake_GEN files...');
loadScript(path.join(FAKE_GEN_DIR, 'data/lists.js'));
loadScript(path.join(FAKE_GEN_DIR, 'js/generators.js'));
loadScript(path.join(FAKE_GEN_DIR, 'js/formatters.js'));
console.log('[LOAD] fake_GEN modules loaded successfully.');

const Generators = context.globalThis.Generators;
const Formatters = context.globalThis.Formatters;

// Define column schemas
const clientColumns = [
  { name: 'client_id', type: 'id', config: { start: 1000, step: 1 } },
  { name: 'name', type: 'fullName', config: {} },
  { name: 'email', type: 'email', config: {} },
  { name: 'country', type: 'country', config: { format: 'name' } }
];

const transactionColumns = [
  { name: 'transaction_id', type: 'id', config: { start: 500000, step: 1 } },
  { name: 'client_id', type: 'integer', config: { min: 1000, max: 10999 } }, // link back to client_id
  { name: 'amount', type: 'float', config: { min: 1, max: 5000, decimals: 2 } },
  { name: 'status', type: 'pattern', config: { pattern: '?' } }, // We'll map this or use simple text
  { name: 'date', type: 'date', config: { min: '2025-01-01', max: '2026-06-01', format: 'YYYY-MM-DD' } }
];

// Helper to generate rows in memory
function generateDataset(columns, count) {
  const rows = [];
  for (let i = 0; i < count; i++) {
    const row = columns.map(col => {
      // Custom handler for transaction status to make it realistic
      if (col.name === 'status') {
        const statuses = ['completed', 'pending', 'failed', 'refunded'];
        return statuses[i % statuses.length];
      }
      return Generators.generate(col, i);
    });
    rows.push(row);
  }
  return rows;
}

// Generate Clients (10,000 rows)
console.log('[GENERATE] Generating 10,000 clients...');
const clientsRows = generateDataset(clientColumns, 10000);
const clientsCsv = Formatters.csv(clientColumns, clientsRows);
fs.writeFileSync(path.join(OUTPUT_DIR, 'clients.csv'), clientsCsv, 'utf8');
console.log(`[OK] Clients written to ${path.join(OUTPUT_DIR, 'clients.csv')} (${clientsCsv.length} bytes)`);

// Generate Transactions (100,000 rows)
console.log('[GENERATE] Generating 100,000 transactions...');
const txRows = generateDataset(transactionColumns, 100000);
const txCsv = Formatters.csv(transactionColumns, txRows);
fs.writeFileSync(path.join(OUTPUT_DIR, 'transactions.csv'), txCsv, 'utf8');
console.log(`[OK] Transactions written to ${path.join(OUTPUT_DIR, 'transactions.csv')} (${txCsv.length} bytes)`);

console.log('[FINISHED] Dataset generation complete!');
