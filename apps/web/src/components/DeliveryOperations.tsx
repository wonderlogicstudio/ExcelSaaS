import {useEffect,useState} from 'react';
import {deliveryRequest} from './DeliveryWorkspace';

type Limits={input_ttl_seconds:number;order_ttl_seconds:number;cleanup_interval_seconds:number;max_execution_attempts:number;purchase_enabled:boolean;durable_commerce_storage:boolean;support_intake_enabled:boolean;automation_mode:string};
export function DeliveryOperations({onNewInput}:{onNewInput:()=>void}){
 const [limits,setLimits]=useState<Limits|null>(null);
 useEffect(()=>{const c=new AbortController();deliveryRequest<Limits>({action:'capabilities'},c.signal).then(setLimits).catch(()=>{});return()=>c.abort()},[]);
 return <section className="delivery-entry shell" aria-label="파일 보관과 다음 작업"><h2>다음 자료도 새로 확인하세요</h2><p>같은 기준을 사용하더라도 새 원본·대상·계산 결과를 다시 확인하고 승인합니다.</p><button type="button" className="button button--outline" onClick={onNewInput}>새 파일 무료 검사 시작</button>
 <details className="delivery-criteria"><summary>보관·취소·지원 범위</summary>{limits?<><p>원본·계획·산출물은 업로드 후 최대 {limits.input_ttl_seconds/60}분입니다. 만료된 파일은 받을 수 없고 {limits.cleanup_interval_seconds}초 주기로 정리합니다. 합성 주문 기록은 {limits.order_ttl_seconds/3600}시간 보관합니다.</p><p>동일 주문의 실행은 처음 실행을 포함해 최대 {limits.max_execution_attempts}회이며, 기술 재시도에는 추가 결제가 없습니다. 변경계획은 계산 후 최대 10분 동안 승인할 수 있습니다. 원본 만료 후에는 같은 원본을 새로 업로드하고 계획을 다시 승인하거나 주문 취소를 요청할 수 있습니다.</p><p>현재는 합성 시험용 임시 저장소입니다. 일반 구매·무인 자동 실행·상담 접수는 제공하지 않습니다. 실제 가격, 환불 조건, 공식 지원 연락처는 운영자 확인 전입니다.</p></>:<p>현재 환경의 보관 설정을 확인하지 못했습니다. 새 납품을 시작하기 전에 상태를 다시 확인하세요.</p>}</details></section>;
}
