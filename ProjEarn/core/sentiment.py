from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def get_mood(text):
    score = analyzer.polarity_scores(text)['compound']
    if score > 0.5:
        return "positive"
    elif score < -0.5:
        return "negative"
    return "neutral"
