import React, { useState } from 'react';
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

function App() {
  const [inputValue, setInputValue] = useState('');
  const [chatHistory, setChatHistory] = useState([]);

  const handleInputChange = (e) => setInputValue(e.target.value);

  const handleSendClick = async () => {
    if (inputValue.trim() !== '') {
      // Add user message to chat history
      const newUserMessage = { sender: 'user', message: inputValue, type: 'text' };
      setChatHistory([...chatHistory, newUserMessage]);

      // Send message to backend and process response
      try {
        const response = await fetch(process.env.REACT_APP_BACKEND_URL + '/chatbot', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: inputValue }),
        });

        if (!response.ok) {
          // Attempt to read the response body even if the status is not OK
          const errorBody = await response.text();
          throw new Error(`HTTP error! status: ${response.status}, body: ${errorBody}`);
        }

        const data = await response.json();
        // Determine the type of response
        const responseType = data.type || 'text';
        const botResponse = { sender: 'bot', message: data.response, type: responseType };
        setChatHistory((prevChatHistory) => [...prevChatHistory, botResponse]);
      } catch (error) {
        console.error('Error sending message to chatbot:', error);
        // Include the error details in the chat history for debugging
        setChatHistory((prevChatHistory) => [...prevChatHistory, { sender: 'bot', message: `Sorry, I encountered an error. Please try again later. Details: ${error.message}`, type: 'text' }]);
      }

      // Reset input field
      setInputValue('');
    }
  };

  const renderChatMessage = (chat) => {
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
              {chatHistory.map((chat, index) => (
                <Box key={index} alignSelf={chat.sender === 'user' ? 'flex-end' : 'flex-start'}>
                  {renderChatMessage(chat)}
                </Box>
              ))}
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
