import express from 'express';
import cors from 'cors';
import { spawn } from 'child_process';
import path from 'path';
import bcrypt from 'bcrypt';
import jwt from 'jwt-simple';
import connectDB from './db';
import { User } from './models/User';
import { History } from './models/History';

const app = express();
const PORT = process.env.PORT || 5000;
const JWT_SECRET = process.env.JWT_SECRET || 'supersecretkey123';

connectDB();

app.use(cors());
app.use(express.json());

// --- Auth Middleware ---
const requireAuth = async (req: any, res: any, next: any) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: "Unauthorized" });
  try {
    const decoded = jwt.decode(token, JWT_SECRET);
    req.user = await User.findById(decoded.id);
    next();
  } catch (err) {
    res.status(401).json({ error: "Invalid token" });
  }
};

// --- Auth Routes ---
app.post('/api/auth/register', async (req, res) => {
  try {
    const { email, password, name } = req.body;
    const existing = await User.findOne({ email });
    if (existing) return res.status(400).json({ error: "Email already in use" });
    
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = await User.create({ email, password: hashedPassword, name });
    const token = jwt.encode({ id: user._id }, JWT_SECRET);
    res.json({ token, user: { id: user._id, name, email } });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    if (!user) return res.status(400).json({ error: "Invalid credentials" });
    
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(400).json({ error: "Invalid credentials" });
    
    const token = jwt.encode({ id: user._id }, JWT_SECRET);
    res.json({ token, user: { id: user._id, name: user.name, email } });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// --- History Routes ---
app.get('/api/history', requireAuth, async (req: any, res) => {
  try {
    const history = await History.find({ user: req.user._id }).sort({ createdAt: -1 });
    res.json(history);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/solve', async (req: any, res: any) => {
    const { equation } = req.body;
    const token = req.headers.authorization?.split(' ')[1];
    let user = null;
    
    if (token) {
        try {
            const decoded = jwt.decode(token, JWT_SECRET);
            user = await User.findById(decoded.id);
        } catch(e) {}
    }

    if (!equation) {
        return res.status(400).json({ success: false, error: "Equation is required" });
    }

    // Path to the python executable in the virtual environment
    const pythonExecutable = process.platform === 'win32' 
        ? path.join(__dirname, 'venv', 'Scripts', 'python.exe')
        : path.join(__dirname, 'venv', 'bin', 'python');
        
    const scriptPath = path.join(__dirname, 'solve_ode.py');

    const pythonProcess = spawn(pythonExecutable, [scriptPath, equation]);

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorString += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.error(`Python script exited with code ${code}`);
            console.error(`Error: ${errorString}`);
            return res.status(500).json({ success: false, error: "Failed to solve equation", details: errorString });
        }
        
        try {
            const result = JSON.parse(dataString);
            
            // Save to history if logged in and successful
            if (result.success && user) {
                History.create({
                    user: user._id,
                    equation: result.equation,
                    type: result.type,
                    solution_latex: result.solution_latex,
                    steps: result.steps
                }).catch(err => console.error("Failed to save history", err));
            }

            res.json(result);
        } catch (error) {
            console.error("Failed to parse JSON from Python:", error);
            res.status(500).json({ success: false, error: "Invalid response from math engine", details: dataString });
        }
    });
});

app.get('/api/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
