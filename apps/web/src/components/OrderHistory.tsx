import {useState} from 'react';
import {deliveryRequest,type DeliveryJob,DeliveryWorkspace} from './DeliveryWorkspace';
import {OrderSummary,artifactLabels,type Order} from './OrderStatus';

export function OrderHistory(){
 const [open,setOpen]=useState(false);const [orders,setOrders]=useState<Order[]>([]);const [resume,setResume]=useState<DeliveryJob|null>(null);const [busy,setBusy]=useState(false);const [error,setError]=useState<string|null>(null);
 const load=async()=>{const result=await deliveryRequest<{orders:Order[]}>({action:'orders'});setOrders(result.orders)};
 const run=async(work:()=>Promise<void>)=>{setBusy(true);setError(null);try{await work()}catch(e){setError(e instanceof Error?e.message:'주문을 확인하지 못했습니다.')}finally{setBusy(false)}};
 const download=(order:Order,kind:string)=>run(async()=>{const f=await deliveryRequest<{filename:string;mime:string;file_base64:string}>({action:order.product_id==='APPROVED_REPAIR'?'download':'comparison_download',job_id:order.job_id,kind});const bytes=Uint8Array.from(atob(f.file_base64),c=>c.charCodeAt(0));const url=URL.createObjectURL(new Blob([bytes],{type:f.mime}));const a=document.createElement('a');a.href=url;a.download=f.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
 return <section className="order-history shell" aria-label="내 합성 테스트 주문"><h2>진행 중인 작업을 이어서 확인하세요</h2><p>이 브라우저 계정의 주문과 파일을 다시 받습니다. 다음 기간의 새 자료는 별도 입력으로 시작하세요.</p><button type="button" className="button button--outline" disabled={busy} onClick={()=>run(async()=>{await load();setOpen(true)})}>{open?'내 주문 새로 확인':'내 테스트 주문 보기'}</button>
 {open&&orders.length===0&&<p role="status">보관 중인 테스트 주문이 없습니다.</p>}{open&&orders.map(order=><article key={order.order_id} className="delivery-step" data-order-id={order.order_id}><h3>{order.product_id==='APPROVED_REPAIR'?'승인 기반 수정':'두 자료 비교'} · {order.order_id.slice(-8)}</h3><OrderSummary order={order}/><div className="delivery-actions">
 {order.artifact_status==='READY'&&order.delivery&&Object.keys(order.delivery.files).map(kind=><button type="button" className="button button--outline" key={kind} disabled={busy} onClick={()=>download(order,kind)}>{artifactLabels[kind]} 다시 받기</button>)}
 {order.product_id==='APPROVED_REPAIR'&&order.entitlement==='ACTIVE'&&order.job_status!=='INPUT_EXPIRED'&&order.artifact_status!=='READY'&&<button type="button" className="button button--primary" disabled={busy} onClick={()=>run(async()=>setResume(await deliveryRequest<DeliveryJob>({action:'get',job_id:order.job_id})))}>변경계획 확인·승인 이어가기</button>}
 {order.entitlement==='ACTIVE'&&order.artifact_status==='QUARANTINED'&&<button type="button" className="button button--outline" disabled={busy} onClick={()=>run(async()=>{await deliveryRequest({action:'retry_delivery',job_id:order.job_id});await load()})}>같은 주문으로 파일 다시 검증</button>}
 {order.job_status==='INPUT_EXPIRED' &&order.payment==='PAID'&&<button type="button" className="button button--outline" onClick={()=>{localStorage.setItem('workbookcare:restore-order',order.order_id);setError('복구할 주문을 선택했습니다. 동일한 원본을 다시 업로드하고 같은 범위를 확인하면 기존 주문으로 연결할 수 있습니다.')}}>동일한 원본 재업로드로 복구</button>}
 <button type="button" className="button button--outline" disabled={busy} onClick={()=>run(async()=>{await deliveryRequest({action:'payment_reconcile' ,order_id:order.order_id});await load()})}>같은 주문 상태 확인</button>
 <button type="button" className="button button--ghost" disabled={busy||order.payment==='CANCELLED'} onClick={()=>run(async()=>{await deliveryRequest({action:'order_cancel',order_id:order.order_id});await load()})}>이 주문 취소</button></div></article>)}
 {resume&&<DeliveryWorkspace key={resume.job_id} initialJob={resume}/>}{error&&<p role="alert">{error}</p>}</section>;
}
