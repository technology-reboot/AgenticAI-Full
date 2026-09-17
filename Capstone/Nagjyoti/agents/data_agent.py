import pandas as pd


class DataAgent:

    REQUIRED_COLUMNS = [
        "symbol",
        "quantity",
        "current_price",
    ]

    def process(
        self,
        file_path: str,
    ) -> dict:

        df = pd.read_csv(file_path)

        missing = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns: {missing}"
            )

        holdings = []

        for _, row in df.iterrows():

            holdings.append(
                {
                    "symbol": str(
                        row["symbol"]
                    ).upper(),

                    "quantity": float(
                        row["quantity"]
                    ),

                    "current_price": float(
                        row["current_price"]
                    )
                }
            )

        return {
            "holdings": holdings
        }