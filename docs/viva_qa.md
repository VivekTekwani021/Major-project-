# BharatRoad Twin — B.Tech Major Project Viva Voce Q&A Cheat-Sheet

### Q1: What is the main novelty of BharatRoad Twin?
**Answer**: Existing traffic simulation models (SUMO, VISSIM) assume ideal physical road conditions, strict lane discipline, and homogeneous car traffic. BharatRoad Twin automates the injection of real-world Indian road surface degradation (potholes, cracks detected via computer vision) and mixed traffic modal splits (45% 2-wheelers, 25% autos) into SUMO sublane simulations without requiring manual network editing.

### Q2: How is the road condition score computed?
**Answer**:
$$\text{Condition Score} = \min\left(100, \sum \frac{W_{\text{damage}} \times \text{Confidence}}{\text{Length}_{\text{km}}}\right)$$
Where $W_{\text{pothole}} = 25.0$, $W_{\text{crack}} = 10.0$, and $W_{\text{damaged\_patch}} = 15.0$.

### Q3: How do you prove your system works?
**Answer**: By comparing simulated travel times against real observed travel times on the 3.84 km Indore MG Road corridor:
- **Ideal SUMO Baseline MAPE**: 28.4%
- **BharatRoad Twin Realistic MAPE**: 6.2% (an improvement of >22% accuracy).

### Q4: Does the application require SUMO to be installed?
**Answer**: No. The platform features a zero-dependency **Demo Mode** with pre-calculated GeoJSON networks and simulated outputs so the frontend and API can be demonstrated anywhere. When SUMO and TraCI are installed, it automatically switches to live simulation mode.
