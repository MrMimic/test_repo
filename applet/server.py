import json

import numpy as np
import pandas as pd

import plotly
from flask import Flask, render_template, request, escape
from plotly import graph_objs as go
from flask_caching import Cache
from sklearn.decomposition import PCA

from c19 import parameters as c19_parameters
from c19 import (database_utilities, embedding, text_preprocessing, query_matching, clusterise_sentences, plot_clusters)

app = Flask(__name__)

# Create cache
config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}
# tell Flask to use the above defined config
app.config.from_mapping(config)
cache = Cache(app)

@cache.cached(timeout=600, key_prefix="all_sentences")
def load_sentence_from_cache(params):
    # Load pre-trained word vectors
    embedding_model = embedding.Embedding(
        parquet_embedding_path=params.embedding.local_path,
        embeddings_dimension=params.embedding.dimension,
        sentence_embedding_method=params.embedding.word_aggregation_method,
        weight_vectors=params.embedding.weight_with_tfidf)

    # Load sentences from SQLite
    all_db_sentences_original = query_matching.get_sentences_data(
        db_path=params.database.local_path)

    return all_db_sentences_original, embedding_model

def get_about():
    about = "Method to write about file to be developped."
    return about

def compute_query_df(params, query):

    # Load cached sentences from SQLite
    all_db_sentences_original, embedding_model = load_sentence_from_cache(params)

    print(query)
    #TODO: increase threshold if too much sentences

    # Get K closest for each
    closest_sentences_df = query_matching.get_k_closest_sentences(
        query=query,
        all_sentences=all_db_sentences_original,
        embedding_model=embedding_model,
        minimal_number_of_sentences=params.query.
        minimum_sentences_kept,
        similarity_threshold=params.query.
        cosine_similarity_threshold)

    # Clusterise them
    closest_sentences_df = clusterise_sentences.perform_kmean(
        k_closest_sentences_df=closest_sentences_df,
        number_of_clusters=params.query.number_of_clusters,
        k_min=params.query.k_min,
        k_max=params.query.k_max,
        min_feature_per_cluster=params.query.
        min_feature_per_cluster)

    return closest_sentences_df

def create_plot(params, df):
    " Method to plot the DF "

    # Reduce vectors dimensions
    pca = PCA(n_components=2)
    # vectors = [json.loads(x) for x in df.vector.to_list()]
    vector_reduced = pca.fit_transform(df.vector.to_list())
    df["x"] = [vector[0] for vector in vector_reduced]
    df["y"] = [vector[1] for vector in vector_reduced]

    # Split raw sentences and join them back with <BR /> for prettier output
    df["sentence_split"] = [
        plot_clusters.add_br_every(s, 7)
        for s in df.raw_sentence.to_list()
    ]

    data = []
    # Here we should get multi scatter foreach cluster with "name" attribute
    # Color as well should be set foreach
    for cluster_id in df["cluster"].unique():
        sub_df = df[df["cluster"] == cluster_id]
        sub_plot = go.Scatter(
            x=sub_df["x"],
            y=sub_df["y"],
            mode="markers",
            hovertext=sub_df["sentence_split"],
            name=f"Cluster {cluster_id}",
            hoverinfo="text"
        )
        data.append(sub_plot)

    # THat stuff should go to a config file
    layout = go.Layout(
        yaxis={"visible": True, "showgrid": True, "zeroline": False, "showticklabels": False},
        xaxis={"visible": True, "showgrid": True, "zeroline": False, "showticklabels": False},
        margin={"l": 50, "r": 50, "b": 50, "t": 20, "pad": 0},
        showlegend=True,
        legend={"orientation": "h"},
        hovermode="closest"
    )

    figure = dict(data=data, layout=layout)
    graphJSON = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

def get_params():

    # Get default parameters and adjust with user's input
    params = c19_parameters.Parameters(
        database=c19_parameters.Database(
            local_path="/home/dynomante/projects/covid-19-kaggle/local_exec/articles_database_v14_02052020_test.sqlite"),
        embedding=c19_parameters.Embedding(
            local_path="/home/dynomante/projects/covid-19-kaggle/w2v_parquet_file_new_version.parquet")
    )

    try:
        params.query.cosine_similarity_threshold = float(request.form["sim_threshold"])
    except KeyError:
        pass
    try:
        params.query.minimum_sentences_kept = int(request.form["n_sentence"])
    except KeyError:
        pass
    try:
        params.query.number_of_clusters = int(request.form["number_cluster"])
    except KeyError:
        pass
    try:
        params.query.min_feature_per_cluster = int(request.form["feature_per_cluster"])
    except KeyError:
        pass

    return params

def detect_json(string):
    try:
        json.loads(string)
        return True
    except (ValueError, json.decoder.JSONDecodeError):
        return False

def validate_query(user_query):
    # Ensure requets
    user_query = escape(user_query)
    # Keep out json
    if detect_json(user_query) is True:
        return None, "Why using JSON?"

    return user_query, "Query processed"

@app.route("/", methods=["GET", "POST"])
def process_user_query():
    # LA methode GET doit juste retourner le template
    # Plutot que le try except du get_param

    # Update params with user's settings
    params = get_params()
    # TODO: up this guy to 0.95 by default
    params.query.cosine_similarity_threshold = 0.95

    # Get query
    # This also should be pre-processed
    default_user_query = "What do we know about Chloroquine to treat covid-19?"
    try:
        user_query = str(request.form["user_query"]) if request.form["user_query"] != "" else default_user_query
    except KeyError:
        user_query = default_user_query

    # Validate user query
    validated_query, message = validate_query(user_query)
    json_plot = None
    if validated_query is not None:
        # Compute sentences DF
        # The heavy part of that stuff is cached
        try:
            closest_sentences_df = compute_query_df(params, validated_query)
            # Create plot from that DF
            json_plot = create_plot(params, closest_sentences_df)
        except Exception as error:
            # TODO: SHould be change into a proper exception in process_query
            # SO we can handle return message differently
            closest_sentences_df = None
            message = f"problem: {error}"

    # Treat DF to get sentences to be plotted.
    output_report = [
        {"number": "Article 1", "title": "Title of the first article", "abstract": "Abstract of the first article"},
        {"number": "Article 2", "title": "Title of the second article",
            "abstract": "Abstract of the second article"}
    ]

    # Create HTML context
    context = {
        "plot": json_plot,
        "output_message": message,
        "about": get_about(),
        "query_last_value": user_query,
        "sim_threshold_last_value": params.query.cosine_similarity_threshold,
        "n_sentence_last_value": params.query.minimum_sentences_kept,
        "number_cluster_last_value": params.query.number_of_clusters,
        "feature_per_cluster_last_value": params.query.min_feature_per_cluster,
        "text_output": output_report
    }

    # Return render
    index_template = render_template("index.html", **context)

    return index_template


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
