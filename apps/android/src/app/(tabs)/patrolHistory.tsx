import { StackScreen } from 'expo-router/build/layouts/stack-utils';
import { StyleSheet, View, Text } from 'react-native';

export default function NotFoundScreen () {
    return (
        <>
            <StackScreen options={{title: 'Patruljehistorik'}} />
            <View style={styles.container}>
                <Text style={styles.text}>
                    Placeholder Patruljehistorik
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