from flask import Flask, render_template, request, jsonify
import page_replacement_simulator

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        frames = int(request.form["frames"])
        pages = list(map(int, request.form["pages"].split()))

        fifo_faults = page_replacement_simulator.fifo(frames, pages)
        lru_faults = page_replacement_simulator.lru(frames, pages)
        optimal_faults = page_replacement_simulator.optimal(frames, pages)

        results = {
            "FIFO Faults": fifo_faults,
            "LRU Faults": lru_faults,
            "Optimal Faults": optimal_faults
        }

    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)
