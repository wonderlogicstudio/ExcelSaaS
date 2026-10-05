"""Specification regression only: does not test WorkbookCare production code."""
import unittest
from contract_oracle import example_context, decide

class ContractTests(unittest.TestCase):
    pass

CASES = [
 ("paid_no_approval","execute",{"approval":"NONE"},False),
 ("reviewed_not_approval","execute",{"approval":"REVIEWED"},False),
 ("valid_repair_execute","execute",{},True),
 ("no_payment","execute",{"payment":"PENDING"},False),
 ("unknown_payment","execute",{"payment":"UNKNOWN"},False),
 ("wrong_sku","execute",{"purchased_product":"TWO_FILE_COMPARISON"},False),
 ("wrong_owner","execute",{"owner_ok":False},False),
 ("stale_plan","execute",{"approval_plan_match":False},False),
 ("expired_approval","execute",{"approval_expired":True},False),
 ("changed_source","execute",{"source_match":False},False),
 ("expired_source","execute",{"source_available":False},False),
 ("no_profile_evidence","execute",{"profile_verified":False},False),
 ("no_patch","execute",{"patch_count":0},False),
 ("failed_prevalidation","execute",{"prevalidation":"FAIL"},False),
 ("not_run_prevalidation","execute",{"prevalidation":"NOT_RUN"},False),
 ("valid_repair_download","download",{},True),
 ("only_report","download",{"artifacts":["change_log","verification_report"]},False),
 ("only_workbook","download",{"artifacts":["repaired_workbook"]},False),
 ("failed_validation","download",{"validation":"FAIL"},False),
 ("not_run_validation","download",{"validation":"NOT_RUN"},False),
 ("quarantined_output","download",{"artifact":"QUARANTINED"},False),
 ("timed_out_job","download",{"job":"TIMED_OUT"},False),
 ("expired_output","download",{"artifact_expired":True},False),
 ("post_refund","download",{"refund":"SUCCEEDED"},False),
 ("refund_pending","publish",{"refund":"PENDING"},False),
 ("late_completion","publish",{"publication_allowed":False},False),
 ("unapproved_execution","download",{"execution_authorized":False},False),
 ("wrong_output_plan","download",{"output_plan_match":False},False),
 ("approval_expired_after_completed_execution","download",{"approval_expired":True},True),
 ("current_source_expired_after_completed_execution","download",{"source_available":False},True),
 ("download_wrong_sku","download",{"purchased_product":"TWO_FILE_COMPARISON"},False),
 ("revoked_entitlement","download",{"entitlement":"REVOKED"},False),
]
for name,action,change,expected in CASES:
    def test(self,a=action,ch=change,e=expected):
        context=example_context(); context.update(ch)
        self.assertEqual(decide(context,a)[0],e)
    setattr(ContractTests,"test_"+name,test)

def comparison_test(self):
    context=example_context("TWO_FILE_COMPARISON")
    context.update(approval="NONE",patch_count=0,plan_ready=False)
    self.assertTrue(decide(context,"execute")[0])
    self.assertTrue(decide(context,"download")[0])
setattr(ContractTests,"test_comparison_has_no_change_approval",comparison_test)

if __name__=="__main__": unittest.main(verbosity=2)
