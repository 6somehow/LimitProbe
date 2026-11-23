| split | paper | S s7 | A | B |
|---|---|---|---|---|
| dev | nnsmith | core | miss | core |
| dev | minference | partial | partial | partial |
| dev | infinigen | miss | miss | miss |
| dev | sparta | miss | miss | miss |
| test-source | prompt-cache | core | core | partial |
| test-source | spinquant | partial | core | miss |
| test-source | kvquant | partial | miss | partial |
| test-source | dx100 | partial | partial | miss |
| paper-only | onesidedmw | core | core | core |
| paper-only | cxlfork | partial | core | partial |
| paper-only | juneberry | partial | core | core |
| paper-only | twilight-tlite | miss | core | miss |

| split | workflow | coverage | core | partial | weighted |
|---|---|---|---|---|---|
| dev | gap_receipt_swarm | 2/4 | 1 | 1 | 3 |
| dev | api_once | 1/4 | 0 | 1 | 1 |
| dev | single_agent | 2/4 | 1 | 1 | 3 |
| test-source | gap_receipt_swarm | 4/4 | 1 | 3 | 5 |
| test-source | api_once | 3/4 | 2 | 1 | 5 |
| test-source | single_agent | 2/4 | 0 | 2 | 2 |
| paper-only | gap_receipt_swarm | 3/4 | 1 | 2 | 4 |
| paper-only | api_once | 4/4 | 4 | 0 | 8 |
| paper-only | single_agent | 3/4 | 2 | 1 | 5 |
