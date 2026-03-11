/**
 * 데이터베이스 스키마 확인 스크립트
 * 사용 가능한 테이블 목록 조회
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://jijifnzcoxglafvjltwn.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imppamlmbnpjb3hnbGFmdmpsdHduIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkyNDY3MTEsImV4cCI6MjA3NDgyMjcxMX0.bDEp8n0z9KGStfVuBlDrfCVScgksI3txnkzomLb-lfo';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

console.log('='.repeat(60));
console.log('데이터베이스 스키마 확인');
console.log('='.repeat(60));

async function checkSchema() {
  // 1. customers 테이블 구조 확인
  console.log('\n[1] customers 테이블 확인');
  const { data: customers, error: custErr } = await supabase
    .from('customers')
    .select('*')
    .limit(1);

  if (custErr) {
    console.log('  ✗ 에러:', custErr.message);
  } else if (customers && customers.length > 0) {
    console.log('  ✓ customers 테이블 컬럼:', Object.keys(customers[0]).join(', '));
  } else {
    console.log('  ⚠ customers 테이블 존재하지만 데이터 없음');
    // 빈 테이블 구조 확인 시도
    const { data: emptyCheck } = await supabase
      .from('customers')
      .select();
    console.log('  테이블 접근 가능:', emptyCheck !== null);
  }

  // 2. 가능한 테이블 목록 시도
  const tablesToCheck = [
    'quotations', 'quotation_items', 'quotes', 'quote_items',
    'products', 'sales', 'sale_items', 'purchases', 'purchase_items',
    'inventory', 'inventory_movements', 'payments', 'tax_invoices',
    'employees', 'departments', 'warehouses', 'bank_accounts',
    'notes', 'payroll', 'journal_entries', 'profiles', 'users'
  ];

  console.log('\n[2] 테이블 존재 여부 확인');

  for (const table of tablesToCheck) {
    const { data, error } = await supabase
      .from(table)
      .select('*')
      .limit(1);

    if (error) {
      if (error.code === 'PGRST205') {
        // 테이블 없음 - 조용히 스킵
      } else {
        console.log(`  ${table}: 에러 - ${error.message}`);
      }
    } else {
      const cols = data && data.length > 0 ? Object.keys(data[0]).length : '?';
      console.log(`  ✓ ${table}: 존재 (컬럼 ${cols}개)`);
      if (data && data.length > 0) {
        console.log(`    샘플 컬럼: ${Object.keys(data[0]).slice(0, 5).join(', ')}...`);
      }
    }
  }

  // 3. 견적 관련 테이블 직접 확인
  console.log('\n[3] 견적 관련 테이블 상세 확인');

  // quotes 테이블 시도
  const { data: quotes, error: quotesErr } = await supabase
    .from('quotes')
    .select('*')
    .limit(3);

  if (!quotesErr && quotes) {
    console.log('  ✓ quotes 테이블 발견!');
    console.log('    컬럼:', quotes.length > 0 ? Object.keys(quotes[0]).join(', ') : '(데이터 없음)');
    console.log('    레코드 수:', quotes.length);
  }

  // estimates 테이블 시도
  const { data: estimates, error: estErr } = await supabase
    .from('estimates')
    .select('*')
    .limit(3);

  if (!estErr && estimates) {
    console.log('  ✓ estimates 테이블 발견!');
    console.log('    컬럼:', estimates.length > 0 ? Object.keys(estimates[0]).join(', ') : '(데이터 없음)');
    console.log('    레코드 수:', estimates.length);
  }

  console.log('\n' + '='.repeat(60));
  console.log('스키마 확인 완료');
  console.log('='.repeat(60));
}

checkSchema().catch(console.error);
