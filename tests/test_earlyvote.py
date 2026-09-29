import io
import tempfile
import unittest
import zipfile
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
