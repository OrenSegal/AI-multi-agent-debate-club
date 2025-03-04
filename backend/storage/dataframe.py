import polars as pl
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import os
import json
import time

class DebateDataFrame:
    """Utility class for data manipulation using Polars dataframes."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    def create_debate_dataframe(self, debates: List[Dict[str, Any]]) -> pl.DataFrame:
        """Create a dataframe from debate data."""
        if not debates:
            return pl.DataFrame()
            
        # Extract the main attributes from debates
        topics = []
        winners = []
        pro_scores = []
        con_scores = []
        timestamps = []
        
        for debate in debates:
            topics.append(debate.get('topic', ''))
            winners.append(debate.get('winner', 'tie'))
            pro_scores.append(debate.get('pro_score', 0))
            con_scores.append(debate.get('con_score', 0))
            timestamps.append(debate.get('timestamp', int(time.time())))
        
        # Create a DataFrame
        df = pl.DataFrame({
            "topic": topics,
            "winner": winners,
            "pro_score": pro_scores,
            "con_score": con_scores,
            "timestamp": timestamps
        })
        
        # Add derived columns for analysis
        df = df.with_columns([
            (pl.col("pro_score") - pl.col("con_score")).alias("score_difference"),
            (pl.col("timestamp").cast(pl.Datetime)).alias("date")
        ])
        
        return df
    
    def save_dataframe(self, df: pl.DataFrame, filename: str) -> bool:
        """Save a dataframe to disk."""
        try:
            file_path = os.path.join(self.data_dir, filename)
            
            # Check file extension and save accordingly
            if filename.endswith('.parquet'):
                df.write_parquet(file_path)
            elif filename.endswith('.csv'):
                df.write_csv(file_path)
            elif filename.endswith('.json'):
                df.write_json(file_path)
            else:
                # Default to parquet
                df.write_parquet(f"{file_path}.parquet")
                
            return True
        except Exception as e:
            print(f"Error saving dataframe: {e}")
            return False
    
    def load_dataframe(self, filename: str) -> Optional[pl.DataFrame]:
        """Load a dataframe from disk."""
        try:
            file_path = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(file_path):
                return None
                
            # Check file extension and load accordingly
            if filename.endswith('.parquet'):
                return pl.read_parquet(file_path)
            elif filename.endswith('.csv'):
                return pl.read_csv(file_path)
            elif filename.endswith('.json'):
                return pl.read_json(file_path)
            else:
                # Try to infer format
                if os.path.exists(f"{file_path}.parquet"):
                    return pl.read_parquet(f"{file_path}.parquet")
                return None
        except Exception as e:
            print(f"Error loading dataframe: {e}")
            return None
    
    def analyze_debates(self, df: pl.DataFrame) -> Dict[str, Any]:
        """Perform analysis on debate data using polars."""
        if df.height == 0:
            return {"message": "No data to analyze"}
            
        results = {}
        
        try:
            # Win rate analysis
            win_counts = df.group_by("winner").agg(pl.count())
            results["win_counts"] = win_counts.to_dicts()
            
            # Score statistics
            score_stats = {
                "pro_score": {
                    "mean": float(df["pro_score"].mean()),
                    "min": int(df["pro_score"].min()),
                    "max": int(df["pro_score"].max())
                },
                "con_score": {
                    "mean": float(df["con_score"].mean()),
                    "min": int(df["con_score"].min()),
                    "max": int(df["con_score"].max())
                }
            }
            results["score_stats"] = score_stats
            
            # Topic frequency
            topic_counts = df.group_by("topic").agg(pl.count()).sort("count", descending=True).limit(10)
            results["popular_topics"] = topic_counts.to_dicts()
            
            # Time series analysis if timestamps are available
            if "date" in df.columns:
                # Get debates by month
                monthly_counts = df.with_columns([
                    pl.col("date").dt.month().alias("month"),
                    pl.col("date").dt.year().alias("year")
                ]).group_by(["year", "month"]).agg(pl.count())
                
                results["timeline"] = monthly_counts.to_dicts()
            
            return results
        except Exception as e:
            print(f"Error in analysis: {e}")
            return {"error": str(e)}
