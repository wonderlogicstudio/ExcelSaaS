import type { ProductOffering } from '../types';
import catalogFixture from '../data/product-catalog.fixture.json';

export const productCatalog = catalogFixture as ProductOffering[];
export const diagnosisCsvArtifact = productCatalog.find((item) => item.product_id === 'FREE_DIAGNOSIS')!
  .deliverables.find((item) => item.kind === 'DIAGNOSIS_CSV')!;

/** An API declaration cannot implement a capability absent from this build. */
export function displayedProducts(remote?: ProductOffering[]): ProductOffering[] {
  return productCatalog.map((local) => {
    const declared = remote?.find((item) => item.product_id === local.product_id);
    const capability = declared?.capability_status ?? local.capability_status;
    return {
      ...local,
      capability_status: capability === 'UNSUPPORTED' ? 'UNSUPPORTED'
        : local.capability_status === 'AVAILABLE' && capability === 'AVAILABLE' ? 'AVAILABLE' : 'PLANNED',
      purchase_enabled: false,
    };
  });
}
