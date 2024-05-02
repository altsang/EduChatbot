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
        return <Text color={chat.sender === 'user' ? 'blue.500' : 'green.500'}>{chat.message}</Text>;
      case 'image':
        return <Image src={chat.message} alt="Chatbot image" />;
      case 'code':
        return <Code children={chat.message} />;
      case 'diagram':
        // Placeholder for diagram rendering
        return <Image src={chat.message} alt="Chatbot diagram" />;
      case 'audio':
        return <audio controls src={chat.message} />;
      case 'video':
        return <video controls width="250">
                 <source src={chat.message} type="video/mp4" />
                 Your browser does not support the video tag.
               </video>;
      case 'interactive':
        return <iframe src={chat.message} width="100%" height="500px" title="Interactive content"></iframe>;
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
