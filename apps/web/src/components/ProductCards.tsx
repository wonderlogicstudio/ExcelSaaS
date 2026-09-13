import type { ProductOffering } from '../types';
import { displayedProducts } from '../lib/products';

const anchors = {
  FREE_DIAGNOSIS: 'diagnosis-product',
  TWO_FILE_COMPARISON: 'two-file-comparison',
  APPROVED_REPAIR: 'approved-repair',
};

export function ProductCards({ products, onStart, onCompare }: { products?: ProductOffering[]; onStart: () => void; onCompare?: () => void }) {
  const synthetic = (product:ProductOffering) => Boolean(onCompare) && product.product_id!=='FREE_DIAGNOSIS' && product.capability_status!=='UNSUPPORTED';
  return (
    <>
      <div className="product-cards">
        {displayedProducts(products).map((product) => (
          <article className="product-card" id={anchors[product.product_id]} key={product.product_id} aria-labelledby={`${product.product_id}-title`}>
            <span className="card-label">{product.capability_status === 'AVAILABLE' ? '현재 제공' : product.capability_status === 'UNSUPPORTED' ? '지원 불가' : synthetic(product) ? '합성 샘플 시험' : '준비 중'}</span>
            <h3 id={`${product.product_id}-title`}>{product.title}</h3>
            <strong className="product-card__boundary">{product.includes_repaired_workbook ? (synthetic(product)?'별도 승인 후 수정본 · 등록된 합성 샘플':'수정본 포함 · 향후 지원 시') : product.product_id === 'TWO_FILE_COMPARISON' ? '비교 보고서 전용 · 수정본 미포함' : '진단 결과 전용 · 수정본 미포함'}</strong>
            <p>{product.scope}</p>
            <h4>{synthetic(product)?'합성 시험에서 받는 파일':product.capability_status === 'AVAILABLE' ? '받는 파일' : '향후 받을 파일 · 현재 제공하지 않음'}</h4>
            <ul className="product-deliverables">{product.deliverables.map((item) => (
              <li key={item.kind}><strong>{item.label}</strong><code>{item.filename}</code></li>
            ))}</ul>
            <h4>포함하지 않는 범위</h4>
            <ul>{product.exclusions.map((item) => <li key={item}>{item}</li>)}</ul>
            <p>{synthetic(product)?'등록된 합성 샘플로 시험할 수 있습니다. 일반 구매는 준비 중입니다.':product.next_action}</p>
            {product.product_id === 'FREE_DIAGNOSIS' ? (
              <button className="button button--primary" type="button" onClick={onStart} disabled={product.capability_status !== 'AVAILABLE'}>무료 진단 시작</button>
            ) : product.product_id === 'TWO_FILE_COMPARISON' && synthetic(product) ? (
              <button className="button button--outline" type="button" onClick={onCompare}>비교 범위 사전 확인</button>
            ) : product.product_id === 'APPROVED_REPAIR' && synthetic(product) ? (
              <button className="button button--outline" type="button" onClick={onStart}>합성 파일 검사 후 수정 범위 확인</button>
            ) : (
              <button className="button button--outline" type="button" disabled>{product.product_id === 'APPROVED_REPAIR' ? '수정 범위 확인' : '두 자료 비교 시작'} · {product.capability_status === 'UNSUPPORTED' ? '지원 불가' : '준비 중'}</button>
            )}
          </article>
        ))}
      </div>
      <div className="product-boundary-note">
        <p><strong>결제 ≠ 변경승인 · 확인함 ≠ 변경승인</strong></p>
        <p>‘확인함/정상으로 판단’은 진단 목록의 개인 처리 상태입니다. 향후 결제를 완료해도 정확한 변경계획을 별도로 승인해야 하며, 현재 일반 고객용 결제·변경승인·수정 실행은 준비 중입니다.</p>
        <p>정밀검증은 향후 판매 패키지에 포함할 검증 활동이며 별도 유료 보고서 상품이 아닙니다. 무료 직접 재검사와 서비스 수정본의 후검증을 구분하며, 후검증은 수정 패키지에 포함됩니다. 자동화 의뢰는 준비 중입니다.</p>
      </div>
    </>
  );
}
