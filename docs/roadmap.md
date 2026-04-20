# TradeLens AI Roadmap

## Milestone 0: Foundation
- initialize repository
- define architecture and module boundaries
- define normalized trading domain models
- define broker adapter interfaces
- choose base tech stack

## Milestone 1: Broker core
- implement broker adapter contract
- add mock broker adapter for development
- add Dhan adapter skeleton
- add Zerodha adapter skeleton
- add Groww adapter skeleton
- implement adapter registry and broker resolution

## Milestone 2: Trading core
- normalized order model
- place / modify / cancel order flows
- orderbook, trades, positions, holdings retrieval
- paper trading mode
- account and portfolio snapshot APIs

## Milestone 3: Risk and observability
- max daily loss guard
- position and symbol exposure limits
- emergency kill switch
- audit logs
- metrics and structured logging

## Milestone 4: Strategy and automation
- webhook ingestion
- rule-based strategies
- scheduling / event-based strategy triggers
- strategy execution history

## Milestone 5: AI intelligence layer
- AI trade journal
- weekly performance summaries
- anomaly detection
- signal ranking
- regime classification

## Milestone 6: Productization
- subscription tiers
- team / advisor workflows
- broker plugin model
- hosted deployment
