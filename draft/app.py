import gunicorn
import flask
import sumy
from flask import Flask, jsonify, request, send_from_directory, render_template, redirect
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer
import nltk
from sumy.utils import get_stop_words
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, TooManyRequests
from nltk.tokenize import sent_tokenize
import os , nltk 
from flask_cors import CORS
from sumy.nlp.tokenizers import Tokenizer
from nltk.tokenize.punkt import PunktSentenceTokenizer




app = Flask(__name__)
CORS(app)

# "Punkt" download before nltk tokenization
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print('Downloading punkt')
    nltk.download('punkt')


# "Wordnet" download before nltk tokenization
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print('Downloading wordnet')
    nltk.download('wordnet' , quiet=True)


# "Stopwords" download before nltk tokenization
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print('Downloading Stopwords')
    nltk.download("stopwords", quiet=True)
    
class TextFormatter:
    def format_transcript(self, transcript):
        lines = [line['text'] for line in transcript]
        formatted_text = ' '.join(lines)
        return formatted_text


def sumy_lsa_summarize(text, percent):
    LANGUAGE = "english"
    SENTENCES_COUNT = int(len(sent_tokenize(text)) * (int(percent) / 100))
   
    parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)

    summarizer = LsaSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(LANGUAGE)

    summary = []
    for sentence in summarizer(parser.document, SENTENCES_COUNT):
        summary.append(str(sentence))
    

    return ' '.join(summary)

def sumy_text_rank_summarize(text, percent):
    LANGUAGE = "english"
    SENTENCES_COUNT = int(len(sent_tokenize(text)) * (int(percent) / 100))

    parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)

    summarizer = TextRankSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(LANGUAGE)

    summary = []
    for sentence in summarizer(parser.document, SENTENCES_COUNT):
        summary.append(str(sentence))
        
    return ' '.join(summary)

@app.route('/transcript-fetch', methods=['GET'])
def transcript_fetch():
    # Get the URL of the current tab
    current_tab_url = request.args.get('current_tab_url')

    # Check if the current tab contains a YouTube video link
    if "youtube.com/watch" in current_tab_url:
        # Extract the video ID from the YouTube link
        video_id = current_tab_url.split("v=")[1].split("&")[0]
        return transcript_fetched_query(video_id)
    else:
        return jsonify(success=False, message="The current tab does not contain a YouTube video link.", response=None), 400

def transcript_fetched_query(video_id):
    # Getting arguments from the request
    choice = request.args.get('choice')  # summarization choice

    
    # Checking whether all parameters exist or not
    if video_id and choice:
        # Every parameter exists here: checking validity of choice
        choice_list = ["sumy-lsa-sum", "sumy-text-rank-sum"]
        if choice in choice_list:
            # Choice is correct: Proceeding with Transcript Fetch and its Summarization
            try:
                # Using Formatter to store and format received subtitles properly.
                formatter = TextFormatter()
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                formatted_text = formatter.format_transcript(transcript).replace("\n", " ")

                # Join the sentences back into a single string
                formatted_text = formatter.format_transcript(transcript).replace("\n", " ")

                # Checking the length of sentences in formatted_text string, before summarizing it.
                tokenizer = PunktSentenceTokenizer()
                sentences = tokenizer.tokenize(formatted_text)

                print("Tokenized Sentences:", sentences)  # Debug statement

                # Checking the length of sentences in formatted_text string, before summarizing it.
                num_sent_text = len(sentences)
                select_length = max(int(num_sent_text * 0.1), 1)  # Getting 10% of the sentences length as select_length
                joined_text = ' '.join(sentences)  # Convert the list of sentences back to a single string
                if choice == "sumy-lsa-sum":
                    summary = sumy_lsa_summarize(joined_text, select_length)
                elif choice == "sumy-text-rank-sum":
                    summary = sumy_text_rank_summarize(joined_text, select_length)
                else:
                    return jsonify(success=False, message="Invalid choice.", response=None), 400
                print("Summary:", summary)  # Debug statement
                return jsonify(success=True, message="Summary generated successfully.", response=summary), 200
            except TranscriptsDisabled:
                return jsonify(success=False, message="The video does not have transcripts enabled.", response=None), 400
            except NoTranscriptFound:
                return jsonify(success=False, message="No transcript found for the video.", response=None), 400
            except VideoUnavailable:
                return jsonify(success=False, message="The video is unavailable.", response=None), 400
            except TooManyRequests:
                return jsonify(success=False, message="Too many requests. Please try again later.", response=None), 400
        else:
            return jsonify(success=False, message="Invalid choice.", response=None), 400
    else:
        return jsonify(success=False, message="Missing parameters.", response=None), 400

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.template_folder = 'templates'
    app.run(debug=True)

