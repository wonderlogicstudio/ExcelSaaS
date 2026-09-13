import {afterEach,expect,it,vi} from 'vitest';
import {deliveryRequest} from '../components/DeliveryWorkspace';
afterEach(()=>vi.unstubAllGlobals());
it('offers a readable retry after a transport failure without changing approval state',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
 await expect(deliveryRequest({action:'capabilities'})).rejects.toMatchObject({code:'NETWORK_UNAVAILABLE',message:'서버에 연결하지 못했습니다. 연결을 확인한 뒤 다시 시도하세요.'});
});
it('preserves an intentional aborted request',async()=>{
 const controller=new AbortController();controller.abort();const error=new DOMException('aborted','AbortError');
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(error));
 await expect(deliveryRequest({action:'capabilities'},controller.signal)).rejects.toBe(error);
});
