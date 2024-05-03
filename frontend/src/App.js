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

  // New useEffect for WebSocket connection setup
  useEffect(() => {
    console.log('Setting up WebSocket connection');
    const newSocket = io(process.env.REACT_APP_BACKEND_URL, {
      reconnectionAttempts: 3,
      reconnectionDelayMax: 10000,
    });
    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('WebSocket connected:', newSocket.connected);
      console.log('WebSocket connection status:', newSocket.connected); // Added console log for connection status
    });

    newSocket.on('connect_error', (error) => {
      console.log('WebSocket connection error:', error);
    });

    newSocket.on('reconnect_attempt', () => {
      console.log('WebSocket attempting to reconnect...');
    });

    return () => {
      console.log('Cleaning up WebSocket connection');
      newSocket.off('connect');
      newSocket.off('connect_error');
      newSocket.off('reconnect_attempt');
      newSocket.close();
    };
  }, []);

  // useEffect for handling chatHistory updates
  useEffect(() => {
    if (socket) {
      const handleMessage = (message) => {
        console.log('handleMessage triggered with message:', message); // Added console log to confirm handleMessage trigger
        console.log('Received message from WebSocket:', message);
        console.log('Message content:', message.response, 'Message type:', message.type); // New log to confirm message content structure
        setChatHistory((prevChatHistory) => {
          const updatedChatHistory = [...prevChatHistory, message];
          console.log('Updated chat history:', updatedChatHistory); // Log to confirm chat history update
          return updatedChatHistory;
        });
      };

      socket.on('response', handleMessage);

      return () => {
        socket.off('response', handleMessage);
      };
    }
  }, [socket]); // Removed chatHistory from the dependency array

  const handleInputChange = (e) => setInputValue(e.target.value);

  const handleSendClick = () => {
    console.log('Attempting to send message:', inputValue); // Added console log for message sending attempt
    if (inputValue.trim() !== '') {
      // Send message to WebSocket server
      socket.emit('message', { message: inputValue });

      console.log('Message sent to WebSocket server:', inputValue);

      // Reset input field
      setInputValue('');
    }
  };

  const renderChatMessage = (chat) => {
    console.log('renderChatMessage called with chat:', chat); // Added console log to confirm renderChatMessage call
    // Determine the type of the chat message for rendering
    let messageType = chat.type; // Assume the backend sends the type
    if (!messageType && chat.response.startsWith("https://")) {
      if (chat.response.endsWith(".mp3")) {
        messageType = 'audio';
      } else if (chat.response.endsWith(".png") || chat.response.endsWith(".jpg") || chat.response.endsWith(".gif")) {
        messageType = 'image';
      } // Add more conditions for other types if needed
    }
    console.log('Rendering chat message:', chat);
    console.log('Rendering message of type:', messageType);
    switch (messageType) {
      case 'text':
        return <Text color={chat.sender === 'user' ? 'blue.500' : 'green.500'}>{chat.response}</Text>;
      case 'image':
        return <Image src={chat.response} alt="Chatbot image" />;
      case 'audio':
        return <audio controls src={chat.response} />;
      case 'code':
        return <Code children={chat.response} />;
      case 'diagram':
        return <Image src={chat.response} alt="Chatbot diagram" />;
      case 'video':
        if (chat.response.includes("youtube.com")) {
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
