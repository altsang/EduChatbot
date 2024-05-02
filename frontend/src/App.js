import React, { useState, useEffect } from 'react';
import {
  ChakraProvider,
  Box,
  Text,
  VStack,
  HStack,
  Grid,
  theme,
  Input,
  Button,
  Image,
  Code,
} from '@chakra-ui/react';
import io from 'socket.io-client';

function App() {
  const [inputValue, setInputValue] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // Connect to WebSocket server
    const newSocket = io(process.env.REACT_APP_BACKEND_URL);
    setSocket(newSocket);

    // Listen for messages from the server
    newSocket.on('message', (message) => {
      console.log('Received message from WebSocket:', message); // Added console log to track incoming messages
      setChatHistory((prevChatHistory) => {
        const updatedChatHistory = [...prevChatHistory, message];
        console.log('Updated chat history:', updatedChatHistory); // Added console log to track chat history updates
        return updatedChatHistory;
      });
    });

    // Log the WebSocket connection status
    newSocket.on('connect', () => {
      console.log('WebSocket connected:', newSocket.connected);
    });

    return () => newSocket.close();
  }, [setSocket]);

  const handleInputChange = (e) => setInputValue(e.target.value);

  const handleSendClick = () => {
    if (inputValue.trim() !== '') {
      // Send message to WebSocket server
      socket.emit('message', { message: inputValue });

      // Reset input field
      setInputValue('');
    }
  };

  const renderChatMessage = (chat) => {
    console.log('Rendering chat message:', chat); // Added console log to track rendering of chat messages
    switch (chat.type) {
      case 'text':
        return <Text color={chat.sender === 'user' ? 'blue.500' : 'green.500'}>{chat.response}</Text>;
      case 'image':
        return <Image src={chat.response} alt="Chatbot image" />;
      case 'code':
        return <Code children={chat.response} />;
      case 'diagram':
        // Placeholder for diagram rendering
        return <Image src={chat.response} alt="Chatbot diagram" />;
      case 'audio':
        return <audio controls src={chat.response} />;
      case 'video':
        // Check if the video URL is from YouTube
        if (chat.response.includes("youtube.com")) {
          // Extract the video ID from the URL
          const videoId = chat.response.split('v=')[1];
          const embedUrl = `https://www.youtube.com/embed/${videoId}`;
          return (
            <iframe
              width="560"
              height="315"
              src={embedUrl}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              title="Video content"
            ></iframe>
          );
        } else {
          // For non-YouTube videos, use the video tag
          return (
            <video controls width="250">
              <source src={chat.response} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          );
        }
      case 'interactive':
        return <iframe src={chat.response} width="100%" height="500px" title="Interactive content"></iframe>;
      // Add cases for other types as needed
      default:
        return <Text color="red.500">Unsupported content type</Text>;
    }
  };

  return (
    <ChakraProvider theme={theme}>
      <Box textAlign="center" fontSize="xl">
        <Grid minH="100vh" p={3}>
          <VStack spacing={8}>
            <Text>Welcome to EduChatbot!</Text>
            <Box w="100%" p={4} borderWidth="1px" borderRadius="lg" overflowY="auto" maxHeight="300px">
              {chatHistory.map((chat, index) => {
                console.log('Mapping chat message:', chat); // Added console log to track mapping of chat messages
                return (
                  <Box key={index} alignSelf={chat.sender === 'user' ? 'flex-end' : 'flex-start'}>
                    {renderChatMessage(chat)}
                  </Box>
                );
              })}
            </Box>
            <HStack>
              <Input
                placeholder="Ask me anything about programming..."
                value={inputValue}
                onChange={handleInputChange}
              />
              <Button colorScheme="blue" onClick={handleSendClick}>
                Send
              </Button>
            </HStack>
          </VStack>
        </Grid>
      </Box>
    </ChakraProvider>
  );
}

export default App;
