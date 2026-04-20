# Dhan Integration Notes

## Current status

The repository includes:

- `DhanApiClient` with HTTP request helpers
- `DhanBrokerAdapter` with normalized domain mapping
- initial tests for payload building and safe default mapping
- environment-based registration through backend settings

## What is already in place

### Client layer
- auth headers
- base URL management
- generic request helper with JSON parsing
- resource helpers for orders, positions, holdings, and funds

### Adapter layer
- normalized `OrderRequest` to broker payload conversion
- normalized `Order`, `Position`, `Holding`, and `FundsSnapshot` mapping
- defensive handling for sparse responses

## Remaining work for a production-ready Dhan adapter

1. Validate exact request payload fields against a live Dhan sandbox or test account
2. Confirm the expected exchange segment values for cash, F&O, and commodities
3. Confirm Dhan-specific product and stop-order semantics
4. Implement direct `get_order(order_id)` retrieval when the endpoint is confirmed
5. Add retries / backoff for transient HTTP errors
6. Add structured logging around broker request failures
7. Add integration tests with mocked HTTP responses

## Immediate next cleanup targets

- tighten outbound mapping for `OrderType.STOP` and `OrderType.STOP_LIMIT`
- map `NSE` and `BSE` more explicitly to Dhan exchange segments
- normalize sparse place-order responses that only return an order id/status
- add dedicated tests for place-order sparse response normalization

## Suggested test matrix

### Order placement
- market buy
- limit buy
- stop market sell
- stop limit sell
- sparse response with only `orderId`

### Account state
- non-empty positions
- non-empty holdings
- funds payload with alternative field names

### Error handling
- 4xx response from broker
- 5xx response from broker
- invalid JSON response
- network timeout
