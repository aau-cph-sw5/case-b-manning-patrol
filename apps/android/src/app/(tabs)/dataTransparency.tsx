import { Stack } from 'expo-router';
import { StyleSheet, View, Text } from 'react-native';

export default function NotFoundScreen () {
    return (
        <>
            <Stack.Screen options={{title: 'Data Gennemsigtighed'}} />
            <View style={styles.container}>
                <Text style={styles.text}>
                    Placeholder Data Gennemsigtighed
                </Text>
            </View>
        </>
    )
}

const styles = StyleSheet.create ({
    container: {
        flex: 1,
        backgroundColor: '#fff',
        justifyContent: 'center',
        alignItems: 'center'
    },

    button: {
        fontSize: 20,
        textDecorationLine: 'underline',
        color: '#25292e'
    },
    
    text: {
        fontSize: 20,
        color: '#25292e'
    }
})