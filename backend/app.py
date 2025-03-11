import os
import random
import sys

import torch
from flask import Flask, request
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app)

move_request = api.model('MoveRequest', {
    'board': fields.List(fields.List(fields.String)),  # 6x7 board
    'difficulty': fields.String(required=True, enum=['easy', 'medium', 'hard'])
})

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, "model", relative_path)

def convert_to_board_state(cols):
    return [cell for col in cols for cell in col]

def find_best_move(board_state, difficulty):
    model_path = resource_path(f"{difficulty}_model.pth")
    model = torch.load(model_path, weights_only=False)
    model.eval()

    cols = [board_state[i::7] for i in range(7)]
    attempted = []

    for col_idx in range(7):
        col = cols[col_idx].copy()
        try:
            row = next(i for i, v in enumerate(col) if v == 0.0 and (i == 5 or col[i+1] != 0))
        except StopIteration:
            continue

        new_col = col.copy()
        new_col[row] = 2.0
        new_cols = cols.copy()
        new_cols[col_idx] = new_col
        new_state = convert_to_board_state(zip(*new_cols))

        with torch.no_grad():
            output = model(torch.tensor(new_state, dtype=torch.float32))
            pred = output.argmax().item()

        attempted.append((new_state, col_idx, pred))

    winning = [a for a in attempted if a[2] == 2]
    ties = [a for a in attempted if a[2] == 0]
    others = [a for a in attempted if a[2] == 1]

    if winning:
        chosen = random.choice(winning)
    elif ties:
        chosen = random.choice(ties)
    elif others:
        chosen = random.choice(others)
    else:
        return None

    return chosen[0], chosen[1]

@api.route('/get-model-move')
class ModelMove(Resource):
    @api.expect(move_request)
    def post(self):
        data = request.json
        frontend_board = data['board']
        difficulty = data['difficulty']

        model_input = []
        for row in frontend_board:
            for cell in row:
                model_input.append(1.0 if cell == 'X' else 2.0 if cell == 'O' else 0.0)

        result = find_best_move(model_input, difficulty)
        if not result:
            return {'error': 'No valid moves'}, 400

        new_state, column = result
        diff = [i for i, (orig, new) in enumerate(zip(model_input, new_state)) if orig != new]
        row = diff[0] // 7 if diff else 0

        return {'row': row, 'column': column}

if __name__ == '__main__':
    app.run(debug=True)