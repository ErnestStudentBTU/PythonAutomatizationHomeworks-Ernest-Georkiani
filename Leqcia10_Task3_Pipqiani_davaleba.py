const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

AWS.config.update({
  region: 'us-east-1'
});

const dynamodb = new AWS.DynamoDB.DocumentClient();

const moodToGenres = {
  "happy": ["Comedy", "Romance", "Adventure"],
  "sad": ["Drama", "Romance"],
  "excited": ["Action", "Adventure", "Thriller"],
  "scary": ["Horror", "Thriller"],
  "thoughtful": ["Drama", "Science Fiction"],
  "intrigued": ["Mystery", "Thriller"],
  "nostalgic": ["Drama", "Romance"],
  "inspired": ["Biography", "Drama"],
  "mysterious": ["Thriller", "Mystery"],
  "action-packed": ["Action", "Adventure", "Science Fiction"]
};

const movies = [
  {
    title: "The Shawshank Redemption",
    year: 1994,
    genre: ["Drama"],
    rating: 9.3,
    director: "Frank Darabont",
    actors: ["Tim Robbins", "Morgan Freeman", "Bob Gunton"],
    plot: "Two imprisoned men bond over a number of years..."
  },
  {
    title: "The Godfather",
    year: 1972,
    genre: ["Crime", "Drama"],
    rating: 9.2,
    director: "Francis Ford Coppola",
    actors: ["Marlon Brando", "Al Pacino", "James Caan"],
    plot: "The aging patriarch of an organized crime dynasty..."
  },
  {
    title: "Pulp Fiction",
    year: 1994,
    genre: ["Crime", "Drama"],
    rating: 8.9,
    director: "Quentin Tarantino",
    actors: ["John Travolta", "Uma Thurman", "Samuel L. Jackson"],
    plot: "The lives of two mob hitmen, a boxer, a gangster..."
  },
  {
    title: "The Dark Knight",
    year: 2008,
    genre: ["Action", "Crime", "Drama"],
    rating: 9.0,
    director: "Christopher Nolan",
    actors: ["Christian Bale", "Heath Ledger", "Aaron Eckhart"],
    plot: "When the menace known as the Joker wreaks havoc..."
  },
  {
    title: "Forrest Gump",
    year: 1994,
    genre: ["Drama", "Romance"],
    rating: 8.8,
    director: "Robert Zemeckis",
    actors: ["Tom Hanks", "Robin Wright", "Gary Sinise"],
    plot: "The presidencies of Kennedy and Johnson, the events of Vietnam..."
  },
  {
    title: "Inception",
    year: 2010,
    genre: ["Action", "Adventure", "Science Fiction"],
    rating: 8.8,
    director: "Christopher Nolan",
    actors: ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"],
    plot: "A thief who steals corporate secrets through the use of dream-sharing..."
  },
  {
    title: "The Matrix",
    year: 1999,
    genre: ["Action", "Science Fiction"],
    rating: 8.7,
    director: "Lana Wachowski, Lilly Wachowski",
    actors: ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
    plot: "A computer hacker learns from mysterious rebels about the true nature of his reality..."
  },
  {
    title: "Goodfellas",
    year: 1990,
    genre: ["Biography", "Crime", "Drama"],
    rating: 8.7,
    director: "Martin Scorsese",
    actors: ["Robert De Niro", "Ray Liotta", "Joe Pesci"],
    plot: "The story of Henry Hill and his life in the mob..."
  },
  {
    title: "The Silence of the Lambs",
    year: 1991,
    genre: ["Crime", "Drama", "Thriller"],
    rating: 8.6,
    director: "Jonathan Demme",
    actors: ["Jodie Foster", "Anthony Hopkins", "Lawrence A. Bonney"],
    plot: "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer..."
  },
  {
    title: "Fight Club",
    year: 1999,
    genre: ["Drama"],
    rating: 8.8,
    director: "David Fincher",
    actors: ["Brad Pitt", "Edward Norton", "Meat Loaf"],
    plot: "An insomniac office worker and a devil-may-care soapmaker form an underground fight club..."
  }
];

async function seedMovies() {
  const tableName = 'Movies';
  
  for (const movie of movies) {
    const params = {
      TableName: tableName,
      Item: {
        movieId: uuidv4(),
        ...movie,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    };
    
    try {
      await dynamodb.put(params).promise();
      console.log(`Added movie: ${movie.title}`);
    } catch (error) {
      console.error(`Error adding movie ${movie.title}:`, error);
    }
  }
}

async function getMoviesByMood(mood) {
  const tableName = 'Movies';
  const genres = moodToGenres[mood.toLowerCase()];
  
  if (!genres) {
    throw new Error('Invalid mood specified');
  }
  
  const params = {
    TableName: tableName
  };
  
  try {
    const result = await dynamodb.scan(params).promise();
    const filteredMovies = result.Items.filter(movie => 
      movie.genre.some(genre => genres.includes(genre))
    );
    
    const shuffled = filteredMovies.sort(() => 0.5 - Math.random());
    return shuffled.slice(0, 2);
  } catch (error) {
    console.error('Error fetching movies by mood:', error);
    throw error;
  }
}

async function main() {
  try {
    await seedMovies();
    
    const mood = 'excited';
    const recommendedMovies = await getMoviesByMood(mood);
    console.log(`\nRecommended movies for ${mood} mood:`);
    recommendedMovies.forEach(movie => {
      console.log(`- ${movie.title} (${movie.year}) [${movie.genre.join(', ')}]`);
    });
  } catch (error) {
    console.error('Error in main:', error);
  }
}

main();