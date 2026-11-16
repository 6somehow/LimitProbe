# Labelling sheets (20 of 51 tested Findings)

Fill `sheet_<you>.csv` alone, without discussing and without opening `key.json` (it holds what the harness said).

* `q1_finding_true`: read the claim, the code location and the quote. Is the claim true of the code at that location?
  `true/false/unclear`. A claim that is true but trivial still counts as true.
* `q2_test_valid`: open the driver (`driver` column, relative to the results root) and read the two runs. Does the test
  show the claim, with the trigger taking the described path and the contrast not taking it, through a call of the
  product's entry or a function the product calls? `valid/invalid/unclear`.
* `notes`: one line when you answer `unclear` or `invalid`.

Then: `python -m checklimits labels evaluate --sheets sheet_r1.csv sheet_r2.csv sheet_r3.csv --key key.json`.
