| split | paper | S s7 | A | B |
|---|---|---|---|---|
| dev | nnsmith | core | miss | miss |
| dev | minference | partial | miss | miss |
| dev | infinigen | miss | miss | miss |
| dev | sparta | miss | miss | miss |
| test-source | prompt-cache | miss | core | miss |
| test-source | spinquant | partial | partial | miss |
| test-source | kvquant | miss | miss | miss |
| test-source | dx100 | partial | partial | miss |
| paper-only | onesidedmw | miss | core | miss |
| paper-only | cxlfork | miss | partial | miss |
| paper-only | juneberry | core | core | core |
| paper-only | twilight-tlite | miss | core | miss |

| split | workflow | coverage | core | partial | weighted |
|---|---|---|---|---|---|
| dev | gap_receipt_swarm | 2/4 | 1 | 1 | 3 |
| dev | api_once | 0/4 | 0 | 0 | 0 |
| dev | single_agent | 0/4 | 0 | 0 | 0 |
| test-source | gap_receipt_swarm | 2/4 | 0 | 2 | 2 |
| test-source | api_once | 3/4 | 1 | 2 | 4 |
| test-source | single_agent | 0/4 | 0 | 0 | 0 |
| paper-only | gap_receipt_swarm | 1/4 | 1 | 0 | 2 |
| paper-only | api_once | 4/4 | 3 | 1 | 7 |
| paper-only | single_agent | 1/4 | 1 | 0 | 2 |
