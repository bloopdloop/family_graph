#!/usr/bin/env node
/**
 * Generate SHA-256 hash for admin password
 * Usage: node scripts/generate_admin_hash.js YOUR_PASSWORD
 */

const crypto = require('crypto');

const password = process.argv[2] || 'family2024';

const hash = crypto.createHash('sha256').update(password).digest('hex');

console.log('');
console.log('🔐 Password Hash Generator');
console.log('=========================');
console.log('');
console.log(`Password: ${password}`);
console.log(`SHA-256:  ${hash}`);
console.log('');
console.log('Copy the hash above and paste it into docs/app.js:');
console.log('ADMIN_PASSWORD_HASH: \'' + hash + '\',');
console.log('');
