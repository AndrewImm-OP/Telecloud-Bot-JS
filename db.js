import { Sequelize, DataTypes } from 'sequelize';

const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: 'database.sqlite3',
  logging: false,
  pool: {
    max: 5,
    min: 0,
    acquire: 30000,
    idle: 10000
  }
});

const User = sequelize.define('User', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  telegram_id: {
    type: DataTypes.BIGINT,
    unique: true,
    allowNull: false
  },
  created_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW
  },
  user_token: {
    type: DataTypes.STRING(255),
    unique: true,
    allowNull: true
  }
}, {
  tableName: 'users',
  timestamps: false
});

async function initDb() {
  await sequelize.authenticate();
  await sequelize.query('PRAGMA journal_mode = WAL;'); 
  await sequelize.sync();
  console.log('Database initialized (WAL mode enabled).');
}

export { User, initDb, sequelize };

