import React, { useState } from 'react'; 
import axios from 'axios'; 


export default function Users() {


    const LoginForm = () => { 
        const [username, setUsername] = useState(''); 
        const [password, setPassword] = useState(''); 
        const [response, setResponse] = useState(''); 
        
        const handleSubmit = async (e) => { 
            e.preventDefault(); 
            
            const data = { username, password }; 
            
            try { 
                const res = await axios.post('http://localhost:5000/login', data);
                setResponse(res.data.response); 
                
                } 
            catch (error) {
                if (error.response) { 
                    setResponse(error.response.data.response)}
                else { 
                    setResponse('Error occurred during login');  }
                }
         }
    
                
        
  return (
    
        <form onSubmit={handleSubmit}>
            <input 
            type='text'
            value={username}
            onChange={(e)=>setUsername(e.target.value)}
            placeholder='UserName'
            />
            <input
            type="password"
            value={password}
            onChange={(e)=>setPassword(e.target.value)}
            placeholder='Password'
            />
            <button type='submit'>Login</button>
            <p>{response}</p>
        </form>
  );
}
    return <LoginForm/>;
}
