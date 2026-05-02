import mongoose from 'mongoose';

const historySchema = new mongoose.Schema({
  user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  equation: { type: String, required: true },
  type: { type: String },
  solution_latex: { type: String },
  steps: [{
    step: String,
    latex: String
  }]
}, { timestamps: true });

export const History = mongoose.model('History', historySchema);
