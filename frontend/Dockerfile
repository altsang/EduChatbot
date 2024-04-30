# Use an official lightweight Node.js runtime as a parent image
FROM node:16-alpine

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json to leverage Docker cache
COPY package*.json ./

# Install app dependencies
RUN npm install --silent

# Copy the rest of the client's source code
COPY . .

# Build the React application
RUN npm run build

# Install serve to serve the production build
RUN npm install -g serve

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Serve the production build of the React application
CMD ["serve", "-s", "build"]
