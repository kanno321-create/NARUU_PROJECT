/**
 * 테이블 컬럼 구조 발견 스크립트
 * 다양한 컬럼명으로 시도하여 실제 스키마 파악
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://jijifnzcoxglafvjltwn.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imppamlmbnpjb3hnbGFmdmpsdHduIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkyNDY3MTEsImV4cCI6MjA3NDgyMjcxMX0.bDEp8n0z9KGStfVuBlDrfCVScgksI3txnkzomLb-lfo';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

console.log('='.repeat(60));
console.log('테이블 컬럼 구조 발견');
console.log('='.repeat(60));

// 가능한 컬럼명 목록
const possibleColumns = [
  'id', 'uuid', 'created_at', 'updated_at',
  'name', 'title', 'description', 'content',
  'status', 'state', 'type', 'category',
  'amount', 'total', 'price', 'value',
  'customer_id', 'user_id', 'client_id',
  'quote_number', 'quotation_number', 'number', 'code',
  'project_name', 'project', 'job_name',
  'supply_amount', 'tax_amount', 'total_amount',
  'valid_until', 'due_date', 'date', 'issued_date',
  'notes', 'memo', 'remarks', 'comment',
];

async function discoverColumns() {
  const tables = ['quotes', 'quote_items', 'customers'];

  for (const table of tables) {
    console.log(`\n[${table}] 테이블 분석`);

    // 방법 1: 컬럼별 select 시도
    const foundColumns = [];

    for (const col of possibleColumns) {
      const { data, error } = await supabase
        .from(table)
        .select(col)
        .limit(1);

      if (!error) {
        foundColumns.push(col);
      }
    }

    if (foundColumns.length > 0) {
      console.log(`  발견된 컬럼: ${foundColumns.join(', ')}`);

      // 전체 데이터 조회로 확인
      const selectCols = foundColumns.join(', ');
      const { data: sample, error: sampleErr } = await supabase
        .from(table)
        .select(selectCols)
        .limit(1);

      if (!sampleErr && sample && sample.length > 0) {
        console.log(`  샘플 데이터:`, JSON.stringify(sample[0], null, 4));
      } else {
        console.log(`  (데이터 없음 - 테이블 비어있음)`);
      }
    } else {
      console.log(`  ✗ 컬럼을 찾을 수 없음 (RLS 또는 접근 권한 문제)`);
    }
  }

  // 방법 2: 빈 객체로 insert 시도 → 에러 메시지에서 필수 컬럼 파악
  console.log('\n' + '-'.repeat(60));
  console.log('Insert 테스트로 필수 컬럼 파악');
  console.log('-'.repeat(60));

  const { data: insertTest, error: insertErr } = await supabase
    .from('quotes')
    .insert({})
    .select();

  if (insertErr) {
    console.log(`\nquotes 빈 insert 에러:`);
    console.log(`  메시지: ${insertErr.message}`);
    console.log(`  힌트: ${insertErr.hint || 'N/A'}`);
    console.log(`  상세: ${insertErr.details || 'N/A'}`);
  }

  console.log('\n' + '='.repeat(60));
  console.log('분석 완료');
  console.log('='.repeat(60));
}

discoverColumns().catch(console.error);
