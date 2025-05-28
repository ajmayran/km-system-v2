from django.db.models import Q
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import string
from appAdmin.models import ResourceMetadata
from django.conf import settings
import os

STOPWORDS_FILE_PATH = os.path.join(
    settings.BASE_DIR,  # Get the base directory of your Django project
    "utils",
    "stopwords",
    "stopwords.txt",
)

# Initialize an empty set for stopwords
custom_stopwords = set()

# Load stopwords if the file exists
if os.path.exists(STOPWORDS_FILE_PATH):
    with open(STOPWORDS_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            custom_stopwords.add(line.strip().lower())
else:
    print(
        f"WARNING: Stopwords file not found at {STOPWORDS_FILE_PATH}. No custom stopwords will be used."
    )


def preprocess_text(text):
    """
    Preprocesses the input text by:
    - Converting to lowercase
    - Removing punctuation
    - Tokenizing (implicitly by splitting, then filtering)
    - Removing custom stopwords
    - Removing extra whitespace
    """
    if not isinstance(text, str):
        return ""  # Handle non-string input gracefully

    # Lowercase
    text = text.lower()
    # print(text) # For debugging, you can keep this or remove

    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Remove extra whitespace and split into words
    words = re.sub(r"\s+", " ", text).strip().split()

    # Remove custom stopwords
    # Only include words that are NOT in our custom_stopwords set
    filtered_words = [word for word in words if word not in custom_stopwords]

    # Join filtered words back into a string
    return " ".join(filtered_words)


def calculate_similarity(text1, text2):
    """
    Calculate cosine similarity between two texts using TF-IDF.

    Args:
        text1 (str): First text string.
        text2 (str): Second text string.

    Returns:
        float: Cosine similarity score as a percentage (0.0 to 100.0).
    """
    if not text1 or not text2:
        return 0.0

    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    similarity = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
    return round(similarity * 100, 2)


def find_similar_resources(input_text, threshold=0.0, print_results=True):
    """
    Find resources with metadata similar to the input text and optionally print them in a tabular format.

    Args:
        input_text (str): Text to compare against resource metadata.
        threshold (float): Minimum similarity percentage to include (0-100).
        print_results (bool): Whether to print the results in tabular form.

    Returns:
        list: List of dictionaries containing resource info and similarity percentages.
    """
    processed_input = preprocess_text(input_text)

    resources = (
        ResourceMetadata.objects.filter(
            Q(title__isnull=False) | Q(description__isnull=False)
        )
        .exclude(Q(title="") & Q(description=""))
        .prefetch_related("tags")
    )  # Optimize tag fetching

    results = []

    for resource in resources:
        title_processed = preprocess_text(resource.title) if resource.title else ""
        desc_processed = (
            preprocess_text(resource.description) if resource.description else ""
        )
        combined_text = f"{title_processed} {desc_processed}".strip()

        title_sim = calculate_similarity(processed_input, title_processed)
        desc_sim = calculate_similarity(processed_input, desc_processed)
        combined_sim = calculate_similarity(processed_input, combined_text)

        if combined_sim >= threshold:
            tag_names = [tag.name for tag in resource.tags.all()]
            results.append(
                {
                    "resource": resource,  # Include the entire model instance
                    "title": resource.title,
                    "slug": resource.slug,
                    "title_similarity": title_sim,
                    "description_similarity": desc_sim,
                    "combined_similarity": combined_sim,
                    "resource_type": str(resource.resource_type),
                    "created_at": resource.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "tags": tag_names,
                }
            )

    results.sort(key=lambda x: x["combined_similarity"], reverse=True)

    return results
