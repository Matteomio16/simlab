import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import pandas as pd

from simlab import earlyvote

HEADER = ("county_desc,voter_reg_num,ncid,voter_last_name,voter_first_name,race,ethnicity,gender,age,"
          "voter_street_address,cong_dist_desc,voter_party_code,ballot_req_delivery_type,ballot_req_type,"
          "ballot_rtn_dt,ballot_rtn_status,sdr")
ROWS = ['WAKE,1,AA1,SMITH,ANN,WHITE,NOT HISPANIC or NOT LATINO,F,71,1 MAIN ST,CONGRESSIONAL DISTRICT 2,DEM,MAIL,MAIL,'
        '09/23/2026,ACCEPTED, ',
        'WAKE,2,AA2,JONES,BOB,WHITE,NOT HISPANIC or NOT LATINO,F,68,2 MAIN ST,CONGRESSIONAL DISTRICT 2,DEM,MAIL,MAIL,'
        '09/23/2026,ACCEPTED, ',
        'DARE,3,AA3,LEE,CY,BLACK or AFRICAN AMERICAN,UNDESIGNATED,M,25,3 MAIN ST,CONGRESSIONAL DISTRICT 3,UNA,'
        'E-MAIL,MAIL,,, ']


class NCCounts(unittest.TestCase):
    def counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("absentee.csv", "\n".join([HEADER, *ROWS]))
            body, voters = earlyvote.nc_counts(path)
        return pd.read_csv(io.BytesIO(body), keep_default_na=False), voters

    def test_only_counts_leave(self):
        d, voters = self.counts()
        self.assertEqual(voters, 3)
        self.assertEqual(list(d.columns), earlyvote.NC_BY + ["n"])
        text = d.to_csv()
        for personal in ("SMITH", "ANN", "MAIN ST", "AA1", "voter_reg_num"):
            self.assertNotIn(personal, text)

    def test_groups_and_bands(self):
        d, _ = self.counts()
        self.assertEqual(d.n.sum(), 3)
        wake = d[d.county_desc == "WAKE"].iloc[0]
        self.assertEqual((wake.n, wake.age_band, wake.ballot_rtn_dt), (2, "65+", "2026-09-23"))
        self.assertEqual(d[d.county_desc == "DARE"].iloc[0].age_band, "18-29")



MAINE_HEADER = ("RES MUNICIPALITY|DES|Voter Record #|P|IB|W-P|CG|SS|SR|DA|CC|Ballot Type|Req Type|Req Date|"
                "Issued Type|Issued Date|Rec Type|Rec Date|Rec Time|DUP|Status|CH|REJ")
MAINE_ROWS = ["Portland||123456|D||1-1|1|27|118|2|3|RB|OR|09/20/2026|MA|09/22/2026|MA|09/28/2026|10:05 AM||ACT||",
              "Portland||123457|D||1-1|1|27|118|2|3|RB|OR|09/20/2026|MA|09/22/2026|MA|09/28/2026|11:00 AM||ACT||",
              "Bangor||223456|R||0-0|2|9|24|3|1|RB|EL|09/21/2026|||||||||"]


class MaineCounts(unittest.TestCase):
    def test_counts_by_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "me.txt"
            path.write_bytes("\n".join([MAINE_HEADER, *MAINE_ROWS]).encode("latin-1"))
            body, n = earlyvote.me_counts(path)
        d = pd.read_csv(io.BytesIO(body), keep_default_na=False, dtype=str)
        self.assertEqual(n, 3)
        self.assertEqual(list(d.columns), earlyvote.MAINE_BY + ["n"])
        portland = d[d.municipality == "Portland"].iloc[0]
        self.assertEqual((portland.n, portland.received, portland.cong_dist, portland.return_status),
                         ("2", "2026-09-28", "1", "ACT"))
        self.assertEqual(d[d.municipality == "Bangor"].iloc[0].received, "")
        self.assertNotIn("123456", d.to_csv())


class IowaLinks(unittest.TestCase):
    def test_general_files_only(self):
        page = ('<a href="https://sos.iowa.gov/sites/default/files/2026-06/ABS%20Counties%202026.pdf">'
                '<a href="https://sos.iowa.gov/sites/default/files/2026-10/ABS%20Counties%202026.pdf">'
                '<a href="https://sos.iowa.gov/sites/default/files/2026-11/ABS%20Counties%202026.pdf">'
                '<a href="https://sos.iowa.gov/sites/default/files/2026-10/ABS%20Congressional%202026.pdf">'
                '<a href="https://sos.iowa.gov/sites/default/files/2026-10/ABS%20State%20House%202026.pdf">')
        with mock.patch.object(earlyvote.requests, "get", return_value=mock.Mock(text=page, raise_for_status=lambda: None)):
            got = earlyvote.iowa()
        self.assertEqual([(n, u.split("/files/")[1]) for n, u, _, _ in got],
                         [("absentee_congressional", "2026-10/ABS%20Congressional%202026.pdf"),
                          ("absentee_counties", "2026-11/ABS%20Counties%202026.pdf")])
        with mock.patch.object(earlyvote.requests, "get", return_value=mock.Mock(text=page[:90], raise_for_status=lambda: None)):
            self.assertEqual(earlyvote.iowa(), [])


if __name__ == "__main__":
    unittest.main()
