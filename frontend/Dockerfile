# Use an official Node.js runtime as a parent image
FROM node

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and install dependencies
COPY package.json package-lock.json /app
RUN npm config set registry https://registry.npmjs.org/
RUN npm install

# Copy the rest of the React app's code
COPY . .

# # Build the app for production
# RUN npm run build

# # Serve the app using a lightweight HTTP server
# RUN npm install -g serve
# EXPOSE 3000
# CMD ["serve", "-s", "build", "-l", "3000"]

#Expose the app's port
EXPOSE 3000

#Run the app when the container is ran
CMD ["npm", "start"]
