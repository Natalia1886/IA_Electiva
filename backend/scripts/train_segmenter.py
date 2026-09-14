"""Train the product-demand segmentation model from digitized sales history.

Feature engineering:
  - sales frequency (units/day, last 30 days)
  - days since the last sale (recency)
  - sales variance (std of daily units, last 60 days)
  - product category (ordinal encoding)
  - correlation with religious dates (demand uplift in the prep window before
    each upcoming feast, computed from previous occurrences)

The model is an explainable **KMeans** on standardized features; the number of
clusters is chosen by the best silhouette score. The output includes the
evaluation metrics (silhouette, Davies-Bouldin, inertia and cluster sizes) so
the quality of the segmentation can be audited.

Usage:
    cd backend && .venv/bin/python -m scripts.train_segmenter
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import engine, async_session_factory
from app.models.holiday import ReligiousHoliday
from app.models.product import Product
from app.services.ai import segmentation

VERSION = "1.0"


async def main() -> None:
    async with engine.begin() as conn:
        from app.database import Base

        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        products = (
            (await db.execute(
                select(Product).options(selectinload(Product.category)).where(Product.is_active.is_(True))
            ))
            .scalars()
            .all()
        )
        holidays = (
            (await db.execute(select(ReligiousHoliday).options(selectinload(ReligiousHoliday.products))))
            .scalars()
            .all()
        )

        rows = await segmentation.feature_rows(db, products, holidays)

    print("=" * 64)
    print("Entrenamiento del modelo de segmentación de demanda")
    print("=" * 64)

    if len(rows) < 3:
        print(f"→ Solo hay {len(rows)} productos con datos; se omiten los artefactos.")
        return

    artifact = segmentation.train_segmenter(rows)
    for metric, value in artifact["metrics"].items():
        print(f"  {metric:<16} {value}")

    print("\nVectores de características (por producto):")
    print("  " + " | ".join(segmentation.FEATURE_COLUMNS))
    for row in rows:
        print(
            f"  {row['code']:<10} "
            + " ".join(f"{row[c]:<9.3f}" if isinstance(row[c], float) else f"{row[c]:<9}" for c in segmentation.FEATURE_COLUMNS)
        )

    print("\nEtiquetas de segmento por velocidad de demanda:")
    for segment_id, label in sorted(artifact["segment_labels"].items(), key=lambda kv: kv[0]):
        print(f"  segmento {segment_id}: demanda {label}")

    path = segmentation.save_segmenter(artifact)
    print(f"\n→ Artefactos guardados en {path}")
    print(f"  (silueta={artifact['metrics']['silhouette']}, "
          f"davies_bouldin={artifact['metrics']['davies_bouldin']}, "
          f"k={artifact['metrics']['k']})")


if __name__ == "__main__":
    asyncio.run(main())