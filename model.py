import random

def predict_prakriti(image_path, answers):

    # Generate random raw scores (dummy)
    vata_score = random.uniform(0.2, 1.0)
    pitta_score = random.uniform(0.2, 1.0)
    kapha_score = random.uniform(0.2, 1.0)

    total = vata_score + pitta_score + kapha_score

    # Convert to percentages
    vata_pct = round((vata_score / total) * 100, 1)
    pitta_pct = round((pitta_score / total) * 100, 1)
    kapha_pct = round((kapha_score / total) * 100, 1)

    dosha_percentages = {
        "Vata": vata_pct,
        "Pitta": pitta_pct,
        "Kapha": kapha_pct
    }

    # Find dominant dosha
    dominant = max(dosha_percentages, key=dosha_percentages.get)

    return {
        "prakriti": dominant,
        "percentages": dosha_percentages
    }
