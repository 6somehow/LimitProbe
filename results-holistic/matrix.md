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

| split | workflow | coverage | core | partial | weighted |
|---|---|---|---|---|---|
| dev | gap_receipt_swarm | 2/4 | 1 | 1 | 3 |
| dev | api_once | 0/4 | 0 | 0 | 0 |
| dev | single_agent | 0/4 | 0 | 0 | 0 |
| test-source | gap_receipt_swarm | 2/4 | 0 | 2 | 2 |
| test-source | api_once | 3/4 | 1 | 2 | 4 |
| test-source | single_agent | 0/4 | 0 | 0 | 0 |
