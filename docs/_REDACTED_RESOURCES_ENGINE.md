# Resource Engine: EmberHeart
Version: 1.1

## 更新顺序 (Authoritative Order)
1. Determine Demand (FU/WU/HU).
2. Compute Node Production (Apply modifiers).
3. Apply Forge Conversion.
4. Apply Caravan Imports.
5. Subtract Consumption.
6. Apply Spoilage.
7. Update Statuses & Morale.

## 消费基数 (Demand)
- **Food/Water**: 305 units each per week.
- **Heat**: Seasonal (0 - 90 HU).
- **Lamp Oil/Ammo**: Operational drain.

## 损耗与容量 (Spoliage)
- **Food Capacity**: 1220 FU. Surplus spoils at 10%/week.
- **Tool Wear**: Increases with heavy labor LU, decreases with Maintenance LU.

#resources #engine #math #emberheart
