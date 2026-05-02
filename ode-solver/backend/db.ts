import mongoose from 'mongoose';

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/odesolver');
    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error: any) {
    console.error(`Error connecting to MongoDB: ${error.message}`);
    console.log('Ensure MongoDB is running locally or set MONGO_URI in .env');
    // We don't exit the process so the math engine can still work without DB during dev
  }
};

export default connectDB;
