# BharatRoad Twin — System Architecture & Data Flow

## 1. System Overview

```
                      +-----------------------------+
                      |    React 18 + Vite UI       |
                      | Leaflet Maps | Recharts UI  |
                      +--------------+--------------+
                                     | REST API / WebSocket
                                     v
                      +-----------------------------+
                      |      FastAPI Backend        |
                      |  (Routers, Services, DB)    |
                      +----+-------------------+----+
                           |                   |
            +--------------+--+             +--+--------------+
            |                 |             |                 |
            v                 v             v                 v
     +--------------+  +------------+ +-----------+   +---------------+
     | Network Bldr |  | Condition  | | SUMO      |   | Validation    |
     | OSMnx + Over |  | Scorer ML  | | TraCI     |   | MAPE / RMSE   |
     +--------------+  +------------+ +-----------+   +---------------+
```

## 2. Condition Penalty Formula
$$\text{Effective Speed} = V_{\text{max}} \times \left(1 - \frac{S_{\text{condition}}}{100} \times \alpha\right)$$

Where:
- $V_{\text{max}}$ is the legal road speed limit.
- $S_{\text{condition}}$ is the edge condition score $[0..100]$.
- $\alpha = 0.5$ is the maximum speed reduction factor.

## 3. Sublane Traffic Model Parameters
To simulate weak lane discipline, SUMO sublane parameters are set to:
- `lateral-resolution`: 0.8 meters
- `minGapLat`: 0.3 meters for 2-wheelers, 0.4 meters for auto-rickshaws
- `latAlignment`: arbitrary (allows free lateral positioning)
