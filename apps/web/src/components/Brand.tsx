import { FileCheck2 } from 'lucide-react';

export function Brand() {
  return (
    <a className="brand" href="#top" aria-label="WorkbookCare 홈">
      <span className="brand__mark" aria-hidden="true">
        <FileCheck2 size={20} strokeWidth={2.2} />
      </span>
      <span className="brand__name">WorkbookCare</span>
      <span className="brand__badge">BETA</span>
    </a>
  );
}
