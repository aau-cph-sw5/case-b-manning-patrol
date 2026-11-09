/** Placeholder screen for the data transparency tab. */
import { Stack } from 'expo-router';
import { StyleSheet, View, Text } from 'react-native';

/**
 * Render the data transparency placeholder.
 *
 * The function name is copied from `+not-found.tsx`; Expo Router only uses the
 * default export, so it does not affect routing.
 */
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